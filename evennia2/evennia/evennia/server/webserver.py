"""
This implements resources for twisted webservers using the wsgi
interface of django. This alleviates the need of running e.g. an
apache server to serve Evennia's web presence (although you could do
that too if desired).

The actual servers are started inside server.py as part of the Evennia
application.

(Lots of thanks to http://githup.com/clemensha/twisted-wsgi-django for
a great example/aid on how to do this.)

"""
import urlparse
from urllib import quote as urlquote
from twisted.web import resource, http, server
from twisted.internet import reactor
from twisted.application import internet
from twisted.web.proxy import ReverseProxyResource
from twisted.web.server import NOT_DONE_YET
from twisted.python import threadpool
from twisted.internet import defer

from twisted.web.wsgi import WSGIResource
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

from evennia.utils import logger

_UPSTREAM_IPS = settings.UPSTREAM_IPS
_DEBUG = settings.DEBUG


class LockableThreadPool(threadpool.ThreadPool):
    """
    Threadpool that can be locked from accepting new requests.
    """

    def __init__(self, *args, **kwargs):
        self._accept_new = True
        threadpool.ThreadPool.__init__(self, *args, **kwargs)

    def lock(self):
        self._accept_new = False

    def callInThread(self, func, *args, **kwargs):
        """
        called in the main reactor thread. Makes sure the pool
        is not locked before continuing.
        """
        if self._accept_new:
            threadpool.ThreadPool.callInThread(self, func, *args, **kwargs)


#
# X-Forwarded-For Handler
#

class HTTPChannelWithXForwardedFor(http.HTTPChannel):
    """
    HTTP xforward class

    """

    def allHeadersReceived(self):
        """
        Check to see if this is a reverse proxied connection.

        """
        CLIENT = 0
        http.HTTPChannel.allHeadersReceived(self)
        req = self.requests[-1]
        client_ip, port = self.transport.client
        proxy_chain = req.getHeader('X-FORWARDED-FOR')
        if proxy_chain and client_ip in _UPSTREAM_IPS:
            forwarded = proxy_chain.split(', ', 1)[CLIENT]
            self.transport.client = (forwarded, port)


# Monkey-patch Twisted to handle X-Forwarded-For.

http.HTTPFactory.protocol = HTTPChannelWithXForwardedFor


class EvenniaReverseProxyResource(ReverseProxyResource):
    def getChild(self, path, request):
        """
        Create and return a proxy resource with the same proxy configuration
        as this one, except that its path also contains the segment given by
        path at the end.

        Args:
            path (str): Url path.
            request (Request object): Incoming request.

        Return:
            resource (EvenniaReverseProxyResource): A proxy resource.

        """
        request.notifyFinish().addErrback(
                lambda f: logger.log_trace("%s\nCaught errback in webserver.py:75." % f))
        return EvenniaReverseProxyResource(
            self.host, self.port, self.path + '/' + urlquote(path, safe=""),
            self.reactor)

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.

        Args:
            request (Request): Incoming request.

        Returns:
            not_done (char): Indicator to note request not yet finished.

        """
        # RFC 2616 tells us that we can omit the port if it's the default port,
        # but we have to provide it otherwise
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = self.proxyClientFactoryClass(
            request.method, rest, request.clientproto,
            request.getAllHeaders(), request.content.read(), request)
        clientFactory.noisy = False
        self.reactor.connectTCP(self.host, self.port, clientFactory)
        # don't trigger traceback if connection is lost before request finish.
        request.notifyFinish().addErrback(
                lambda f: logger.log_trace("%s\nCaught errback in webserver.py:75." % f))
        return NOT_DONE_YET


#
# Website server resource
#


class DjangoWebRoot(resource.Resource):
    """
    This creates a web root (/) that Django
    understands by tweaking the way
    child instances are recognized.
    """

    def __init__(self, pool):
        """
        Setup the django+twisted resource.

        Args:
            pool (ThreadPool): The twisted threadpool.

        """
        self.pool = pool
        self._echo_log = True
        self._pending_requests = {}
        resource.Resource.__init__(self)
        self.wsgi_resource = WSGIResource(reactor, pool, WSGIHandler())

    def empty_threadpool(self):
        """
        Converts our _pending_requests list of deferreds into a DeferredList

        Returns:
            deflist (DeferredList): Contains all deferreds of pending requests.

        """
        self.pool.lock()
        if self._pending_requests and self._echo_log:
            self._echo_log = False  # just to avoid multiple echoes
            msg = "Webserver waiting for %i requests ... "
            logger.log_info(msg % len(self._pending_requests))
        return defer.DeferredList(self._pending_requests, consumeErrors=True)

    def _decrement_requests(self, *args, **kwargs):
        self._pending_requests.pop(kwargs.get('deferred', None), None)

    def getChild(self, path, request):
        """
        To make things work we nudge the url tree to make this the
        root.

        Args:
            path (str): Url path.
            request (Request object): Incoming request.

        Notes:
            We make sure to save the request queue so
            that we can safely kill the threadpool
            on a server reload.

        """
        path0 = request.prepath.pop(0)
        request.postpath.insert(0, path0)

        deferred = request.notifyFinish()
        self._pending_requests[deferred] = deferred
        deferred.addBoth(self._decrement_requests, deferred=deferred)

        return self.wsgi_resource


#
# Site with deactivateable logging
#

class Website(server.Site):
    """
    This class will only log http requests if settings.DEBUG is True.
    """
    noisy = False

    def logPrefix(self):
        "How to be named in logs"
        if hasattr(self, "is_portal") and self.is_portal:
            return "Webserver-proxy"
        return "Webserver"

    def log(self, request):
        """Conditional logging"""
        if _DEBUG:
            server.Site.log(self, request)


#
# Threaded Webserver
#

class WSGIWebServer(internet.TCPServer):
    """
    This is a WSGI webserver. It makes sure to start
    the threadpool after the service itself started,
    so as to register correctly with the twisted daemon.

    call with WSGIWebServer(threadpool, port, wsgi_resource)

    """

    def __init__(self, pool, *args, **kwargs):
        """
        This just stores the threadpool.

        Args:
            pool (ThreadPool): The twisted threadpool.
            args, kwargs (any): Passed on to the TCPServer.

        """
        self.pool = pool
        internet.TCPServer.__init__(self, *args, **kwargs)

    def startService(self):
        """
        Start the pool after the service starts.

        """
        internet.TCPServer.startService(self)
        self.pool.start()

    def stopService(self):
        """
        Safely stop the pool after the service stops.

        """
        internet.TCPServer.stopService(self)
        self.pool.stop()

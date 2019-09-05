"""
Webclient based on websockets.

This implements a webclient with WebSockets (http://en.wikipedia.org/wiki/WebSocket)
by use of the txws implementation (https://github.com/MostAwesomeDude/txWS). It is
used together with evennia/web/media/javascript/evennia_websocket_webclient.js.

All data coming into the webclient is in the form of valid JSON on the form

`["inputfunc_name", [args], {kwarg}]`

which represents an "inputfunc" to be called on the Evennia side with *args, **kwargs.
The most common inputfunc is "text", which takes just the text input
from the command line and interprets it as an Evennia Command: `["text", ["look"], {}]`

"""
import re
import json
from twisted.internet.protocol import Protocol
from django.conf import settings
from evennia.server.session import Session
from evennia.utils.utils import to_str, mod_import
from evennia.utils.ansi import parse_ansi
from evennia.utils.text2html import parse_html

_RE_SCREENREADER_REGEX = re.compile(r"%s" % settings.SCREENREADER_REGEX_STRIP, re.DOTALL + re.MULTILINE)
_CLIENT_SESSIONS = mod_import(settings.SESSION_ENGINE).SessionStore


class WebSocketClient(Protocol, Session):
    """
    Implements the server-side of the Websocket connection.
    """
    def __init__(self, *args, **kwargs):
        super(WebSocketClient, self).__init__(*args, **kwargs)
        self.protocol_key = "webclient/websocket"

    def connectionMade(self):
        """
        This is called when the connection is first established.

        """
        self.transport.validationMade = self.validationMade
        client_address = self.transport.client
        client_address = client_address[0] if client_address else None
        self.init_session("websocket", client_address, self.factory.sessionhandler)

    def get_client_session(self):
        """
        Get the Client browser session (used for auto-login based on browser session)

        Returns:
            csession (ClientSession): This is a django-specific internal representation
                of the browser session.

        """
        try:
            self.csessid = self.transport.location.split("?", 1)[1]
        except IndexError:
            # this may happen for custom webclients not caring for the
            # browser session.
            self.csessid = None
            return None
        if self.csessid:
            return _CLIENT_SESSIONS(session_key=self.csessid)

    def validationMade(self):
        """
        This is called from the (modified) txws websocket library when
        the ws handshake and validation has completed fully.

        """
        csession = self.get_client_session()
        uid = csession and csession.get("webclient_authenticated_uid", None)
        if uid:
            # the client session is already logged in.
            self.uid = uid
            self.logged_in = True

        # watch for dead links
        self.transport.setTcpKeepAlive(1)
        # actually do the connection
        self.sessionhandler.connect(self)

    def disconnect(self, reason=None):
        """
        Generic hook for the engine to call in order to
        disconnect this protocol.

        Args:
            reason (str): Motivation for the disconnection.

        """
        self.data_out(text=((reason or "",), {}))

        csession = self.get_client_session()

        if csession:
            csession["webclient_authenticated_uid"] = None
            csession.save()
            self.logged_in = False
        self.connectionLost(reason)

    def connectionLost(self, reason):
        """
        This is executed when the connection is lost for whatever
        reason. it can also be called directly, from the disconnect
        method.

        Args:
            reason (str): Motivation for the lost connection.

        """
        self.sessionhandler.disconnect(self)
        self.transport.close()

    def dataReceived(self, string):
        """
        Method called when data is coming in over the websocket
        connection. This is always a JSON object on the following
        form:
            [cmdname, [args], {kwargs}]


        """
        cmdarray = json.loads(string)
        if cmdarray:
            self.data_in(**{cmdarray[0]: [cmdarray[1], cmdarray[2]]})

    def sendLine(self, line):
        """
        Send data to client.

        Args:
            line (str): Text to send.

        """
        return self.transport.write(line)

    def at_login(self):
        csession = self.get_client_session()
        if csession:
            csession["webclient_authenticated_uid"] = self.uid
            csession.save()

    def data_in(self, **kwargs):
        """
        Data User > Evennia.

        Args::
            text (str): Incoming text.
            kwargs (any): Options from protocol.

        Notes:
            At initilization, the client will send the special
            'csessid' command to identify its browser session hash
            with the Evennia side.

            The websocket client will also pass 'websocket_close' command
            to report that the client has been closed and that the
            session should be disconnected.

            Both those commands are parsed and extracted already at
            this point.

        """

        if "websocket_close" in kwargs:
            self.disconnect()
            return

        self.sessionhandler.data_in(self, **kwargs)

    def data_out(self, **kwargs):
        """
        Data Evennia->User.

        Kwargs:
            kwargs (any): Options ot the protocol
        """
        self.sessionhandler.data_out(self, **kwargs)

    def send_text(self, *args, **kwargs):
        """
        Send text data. This will pre-process the text for
        color-replacement, conversion to html etc.

        Args:
            text (str): Text to send.

        Kwargs:
            options (dict): Options-dict with the following keys understood:
                - raw (bool): No parsing at all (leave ansi-to-html markers unparsed).
                - nocolor (bool): Clean out all color.
                - screenreader (bool): Use Screenreader mode.
                - send_prompt (bool): Send a prompt with parsed html

        """
        if args:
            args = list(args)
            text = args[0]
            if text is None:
                return
        else:
            return

        flags = self.protocol_flags
        text = to_str(text, force_string=True)

        options = kwargs.pop("options", {})
        raw = options.get("raw", flags.get("RAW", False))
        nocolor = options.get("nocolor", flags.get("NOCOLOR", False))
        screenreader = options.get("screenreader", flags.get("SCREENREADER", False))
        prompt = options.get("send_prompt", False)

        if screenreader:
            # screenreader mode cleans up output
            text = parse_ansi(text, strip_ansi=True, xterm256=False, mxp=False)
            text = _RE_SCREENREADER_REGEX.sub("", text)
        cmd = "prompt" if prompt else "text"
        if raw:
            args[0] = text
        else:
            args[0] = parse_html(text, strip_ansi=nocolor)

        # send to client on required form [cmdname, args, kwargs]
        self.sendLine(json.dumps([cmd, args, kwargs]))

    def send_prompt(self, *args, **kwargs):
        kwargs["options"].update({"send_prompt": True})
        self.send_text(*args, **kwargs)

    def send_default(self, cmdname, *args, **kwargs):
        """
        Data Evennia -> User.

        Args:
            cmdname (str): The first argument will always be the oob cmd name.
            *args (any): Remaining args will be arguments for `cmd`.

        Kwargs:
            options (dict): These are ignored for oob commands. Use command
                arguments (which can hold dicts) to send instructions to the
                client instead.

        """
        if not cmdname == "options":
            self.sendLine(json.dumps([cmdname, args, kwargs]))

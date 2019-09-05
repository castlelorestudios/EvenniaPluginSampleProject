import json
import time
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import protocol
from django.conf import settings
from evennia.server.session import Session
from twisted.application import internet
from evennia.utils.utils import to_str, mod_import
from evennia.utils.ansi import strip_ansi, ANSI_PARSER

_CLIENT_SESSIONS = mod_import(settings.SESSION_ENGINE).SessionStore
_UE4PORT = settings.UE4PORT
_UE4ADDR = settings.UE4ADDR

class UnrealPlugin(Protocol, Session):

    def __init__(self):    
        #print("UnrealPlugin init for port: {}".format(_UE4PORT))
        self.protocol_key = "UnrealPlugin"

    def connectionMade(self):
        #print("UnrealPlugin connectionMade")
        client_address = self.transport.client
        client_address = client_address[0] if client_address else None

        self.init_session("UnrealPlugin", client_address, self.factory.sessionhandler)
        self.set_properties()
        self.csessid = ""
        self.connected = False
        self.ackSent = False
        self.header = ""

        #print("UnrealPlugin end of connectionMade")

    def set_properties(self):
        self.protocol_flags = {"ENCODING": "utf-8",
                               "SCREENREADER": False,
                               "INPUTDEBUG": False,
                               "RAW": True,
                               "NOCOLOR": True}

    def delayed_restore_session(self):
        #print("UnrealPlugin delayed_restore_session start")
        sess = self.sessionhandler.sessions_from_csessid(self.csessid)
        if sess:
            #print("UnrealPlugin connectionMade previous session found")
            sess = sess[0]
            self.sessid = sess.sessid
            self.uid = sess.uid
            self.logged_in = sess.logged_in
            self.sessionhandler.sync(sess)
        else:
            #print("UnrealPlugin delayed_restore_session no session found")
            self.sessionhandler.connect(self)

        self.set_properties()
        self.connected = True
        self.transport.setTcpKeepAlive(1)
        #print("UnrealPlugin delayed_restore_session end")

    def get_client_session(self):
        #print("UnrealPlugin get_client_session")
        if self.csessid:
            return _CLIENT_SESSIONS(session_key=self.csessid)

    def at_login(self):
        #print("UnrealPlugin at_login. Uid: {}".format(self.uid))
        csession = self.get_client_session()
        if csession:
            #print("UnrealPlugin at_login csession found")
            csession["webclient_authenticated_uid"] = self.uid
            csession.save()
        self.set_properties()
        #print("UnrealPlugin at_login end")

    def connectionLost(self, reason):
        #self.sessionhandler.disconnect(self)
        self.transport.write("UnrealPlugin connectionLost")

    def data_in(self, **kwargs):
        #print("UnrealPlugin data_in(kwargs): " + json.dumps(kwargs))
        self.sessionhandler.data_in(self, **kwargs)

    def data_out(self, **kwargs):
        #print("UnrealPlugin data_out")
        self.sessionhandler.data_out(self, **kwargs)
        seq_data = json.dumps(kwargs)
        if seq_data: 
            #print("UnrealPlugin data_out: data received from Evennia: " + seq_data)
            if self.header:
                #print("Property flags: {}".format(self.protocol_flags))
                #print("UnrealPlugin data_out: prefixing data with header: " + self.header)
                seq_data = self.header + seq_data
            self.transport.write(seq_data)
        else:
            self.transport.write("UnrealPlugin data_out: serialization of data from Evennia failed")

    def dataReceived(self, data):
        #print("UnrealPlugin dataReceived: |" + data + "|")
        if data.startswith('GUID['):
            end = data.find(']')
            if end > 0:
                guid = data[5:end]
                data = data[end + 1:]
                #print("UnrealPlugin dataReceived GUID found: " + guid)  
                hdr = "ACK[" + guid + "]"                  

                if hdr != self.header:
                    self.header = hdr
                    self.ackSent = False

                if self.connected == False:
                    #print("UnrealPlugin dataReceived About to connect session")  
                    self.csessid = guid
                    self.delayed_restore_session()
                #else:
                    #print("UnrealPlugin dataReceived session already connected")  

        cmdarray = json.loads(data)
        if cmdarray:
            #print("UnrealPlugin dataReceived: about to call data_in")
            self.data_in(**{cmdarray[0]: [cmdarray[1], cmdarray[2]]})
        #else:
            #print("UnrealPlugin dataReceived: JSON load failed")

    def sendLine(self, line):
        #parse_ansi(line, strip_ansi=True, xterm256=False, mxp=False)
        if self.header and self.ackSent == False:
            self.ackSent = True
            #print("UnrealPlugin sendLine: prefixing data with header: " + self.header)
            line = self.header + line
        line = line + "<EOF>"
        line = strip_ansi(line, parser=ANSI_PARSER)
        #print("UnrealPlugin sendLine: " + line)
        return self.transport.write(line)

    def send_default(self, cmdname, *args, **kwargs):
        #print("UnrealPlugin send_default")
        if not cmdname == "options":
            self.sendLine(json.dumps([cmdname, args, kwargs]))

    #def doStart(self):
    #    #print("doStart called")

def start_plugin_services(portal):

        #print("In start_plugin_services")

        w_interface = _UE4ADDR
        w_ifacestr = "-%s" % _UE4PORT
        port = _UE4PORT

        class UnrealPluginFactory(protocol.ServerFactory):
            "Only here for better naming in logs"
            pass

        factory = UnrealPluginFactory()
        factory.noisy = True
        factory.protocol = UnrealPlugin
        factory.sessionhandler = portal.sessions
        factory.name = "UnrealPluginFactory"

        my_service = internet.TCPServer(port, factory)

        # all Evennia services must be uniquely named
        my_service.setName("UnrealPluginService")

        # add to the main portal application
        portal.services.addService(my_service)

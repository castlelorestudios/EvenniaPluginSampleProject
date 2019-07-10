from twisted.internet.protocol import Protocol, Factory
from twisted.application import internet

class EchoFactory(Factory):

    def __init__(self):
        print("EchoFactory init")

    def buildProtocol(self, addr):
        return Echo()

    noisy = False

    def logPrefix(self):
        return "Echo"

class Echo(Protocol):

    def __init__(self):
        print("Echo init")
        self.protocol_key = "Echo"
        self.factory = EchoFactory

    def connectionMade(self):
        self.transport.write("Welcome to Echo server")

    def connectionLost(self, reason):
        self.transport.write("Connection lost to ")

    def dataReceived(self, data):
        self.transport.write("Echo: " + data)

    def doStart(self):
        print("doStart called")

def start_plugin_services(portal):

        print("In start_plugin_services")
        factory = EchoFactory()
        my_service = internet.TCPServer(8000, factory)

        # all Evennia services must be uniquely named
        my_service.setName("EchoService")

        # add to the main portal application
        portal.services.addService(my_service)


import threading, SocketServer, logging
#from Lib.ObjectFormatting import flatten
from Lib.ParameterChecking import checkType, checkAttr, checkIPv4, checkPort, checkOptions
from Session import Session

class IPFIX_UDP_Handler(SocketServer.DatagramRequestHandler):
    IPFIX_SESSION = None
    def handle(self):
        #logger = logging.getLogger(__name__)
        #logger.debug('Client %s:%d:' % self.client_address)
        message = IPFIX_UDP_Handler.IPFIX_SESSION.readMessage(
                        self.rfile, self.client_address[0], self.client_address[1])
        #logger.debug('  Message: %s' % flatten(message))

class Collector(object):
    def __init__(self, session):
        checkType('session', (Session,), session)
        self.__logging = logging.getLogger(__name__)
        self.__configured = False
        self.__running = False
        self.__listenIP = None
        self.__listenPort = None
        self.__transport = None
        self.__session = session
        self.__server = None
        self.__serverThread = None
    
    def isConfigured(self): return(self.__configured)
    def isRunning(self):    return(self.__running)
    def getSession(self): return(self.__session)

    @staticmethod
    def checkConfiguration(config):
        checkType('config', (dict,), config)
        checkIPv4('listenIP', checkAttr('listenIP', config))
        checkPort('listenPort', checkAttr('listenPort', config))
        
        transport = checkAttr('transport', config)
        checkOptions('transport', transport, ['udp', 'tcp'])
        if(transport != 'udp'): raise Exception('Transport(%s) not implemented' % str(transport))

    def configure(self, config):
        Collector.checkConfiguration(config)
        self.__listenIP = config['listenIP']
        self.__listenPort = config['listenPort']
        self.__transport = config['transport']
        self.__configured = True

    def updateTemplate(self, template, domainId=None):
        if((len(self.__session.getDomainIds()) == 0) and (domainId is None)):
            raise Exception('Unable to update template in all domains since Session does not has any domain')
        
        domainIds = [domainId] if(domainId is not None) else self.__session.getDomainIds()
        for obsDomId in domainIds:
            domain = self.__session.getDomain(obsDomId)
            domain.updateCollectorTemplate(template)

    def start(self):
        if(not self.__configured): return
        if(self.__running): return
        if(self.__transport == 'udp'):
            IPFIX_UDP_Handler.IPFIX_SESSION = self.__session
            SocketServer.UDPServer.max_packet_size = 128 * 1024
            self.__server = SocketServer.UDPServer((self.__listenIP, self.__listenPort), IPFIX_UDP_Handler)
        else:
            raise Exception('Unsupported transport: %s' % self.__transport)

        self.__serverThread = threading.Thread(target=self.__server.serve_forever)
        self.__serverThread.setDaemon(True)
        self.__serverThread.start()
        
        logger = logging.getLogger(__name__)
        logger.info('Server listening on %s:%s:%d' % ((self.__transport,) + self.__server.server_address))
        self.__running = True
    
    def stop(self):
        if(not self.__running): return
        self.__server.shutdown()
        self.__server.server_close()
        self.__serverThread.join()
        self.__running = False

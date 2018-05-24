import threading, socket, logging
from cStringIO import StringIO
from Lib.ParameterChecking import checkType, checkAttr, checkIPv4, checkPort,\
                                  checkOptions, checkFloat
from Session import Session
from Message import Message

class Exporter(object):
    def __init__(self, session):
        checkType('session', (Session,), session)
        self.__configured = False
        self.__running = False
        self.__session = session
        self.__client = None
        self.__localIP = None
        self.__serverIP = None
        self.__serverPort = None
        self.__transport = None
        self.__templateRefreshTimeout = None
        self.__timer = None
    
    @staticmethod
    def checkConfiguration(config):
        checkType('config', (dict,), config)
        checkIPv4('localIP', checkAttr('localIP', config))
        checkIPv4('serverIP', checkAttr('serverIP', config))
        checkPort('serverPort', checkAttr('serverPort', config))
        
        transport = checkAttr('transport', config)
        checkOptions('transport', transport, ['udp', 'tcp'])
        if(transport != 'udp'): raise Exception('Transport(%s) not implemented' % str(transport))

        checkFloat('templateRefreshTimeout', checkAttr('templateRefreshTimeout', config), 1, 86400)
        
    def configure(self, config):
        Exporter.checkConfiguration(config)
        self.__localIP = config['localIP']
        self.__serverIP = config['serverIP']
        self.__serverPort = config['serverPort']
        self.__transport = config['transport']
        self.__templateRefreshTimeout = config['templateRefreshTimeout']
        self.__configured = True
    
    def reconfigure(self, serverIP, serverPort):
        checkIPv4('serverIP', serverIP)
        checkPort('serverPort', serverPort)
        self.__serverIP = serverIP
        self.__serverPort = serverPort

        if(not self.__configured): return
        
        for obsDomId in self.__session.getDomainIds():
            domain = self.__session.getDomain(obsDomId)
            domain.getExporterSequentiation().reset()

        if(not self.__running): return
        self.stop()
        self.start()
    
    def updateTemplate(self, template, domainId=None):
        if((len(self.__session.getDomainIds()) == 0) and (domainId is None)):
            raise Exception('Unable to update template in all domains since Session does not has any domain')
        
        domainIds = [domainId] if(domainId is not None) else self.__session.getDomainIds()
        for obsDomId in domainIds:
            domain = self.__session.getDomain(obsDomId)
            domain.updateExporterTemplate(template)

    def isConfigured(self): return(self.__configured)
    def isRunning(self): return(self.__running)
    def getSession(self): return(self.__session)
    
    def refreshTemplates(self, domainId=None, templateId=None):
        obsDomIds = self.__session.getDomainIds()
        if(domainId is not None):
            if(domainId not in obsDomIds): return
            obsDomIds = [domainId]
        
        for obsDomId in obsDomIds:
            domain = self.__session.getDomain(obsDomId)
            templateIds = domain.getExporterTemplateIds()
            if(templateId is not None):
                if(templateId not in templateIds): continue
                templateIds = [templateId]
            if(len(templateIds) == 0): continue
            message = Message.create(self.__session, obsDomId)
            templateSet = message.addTemplateSet()
            for templateId in templateIds:
                template = domain.getExporterTemplate(templateId)
                templateSet.addRecord(template)
            self.sendMessage(message)

    def _refreshTemplates(self):
        self.refreshTemplates()
        self._startRefreshTemplateTimer()

    def _startRefreshTemplateTimer(self):
        self.__timer = threading.Timer(self.__templateRefreshTimeout, self._refreshTemplates)
        self.__timer.setDaemon(True)
        self.__timer.start()

    def start(self):
        if(not self.__configured): return
        if(self.__running): return
        if(self.__transport == 'udp'):
            self.__client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if((self.__localIP != '0.0.0.0') and (not self.__localIP.startswith('127.'))):
                self.__client.bind((self.__localIP, 0))
        else:
            raise Exception('Unsupported transport: %s' % self.__transport)
        
        logger = logging.getLogger(__name__)
        logger.info('Client sending to %s:%s:%d' % (self.__transport, self.__serverIP, self.__serverPort))
        
        self._refreshTemplates()
        self.__running = True
    
    def stop(self):
        if(not self.__running): return
        if(self.__transport == 'udp'):
            pass
        elif(self.__transport == 'tcp'):
            self.__client.shutdown(socket.SHUT_RDWR)
        else:
            pass
        self.__client.close()
        self.__timer.cancel()
        self.__running = False
    
    def sendMessage(self, message):
        if(self.__transport == 'udp'):
            wfile = StringIO()
            self.__session.writeMessage(message, wfile)
            self.__client.sendto(wfile.getvalue(), (self.__serverIP, self.__serverPort))
        elif(self.__transport == 'tcp'):
            wfile = self.__client.makefile('wb', 0)
            self.__session.writeMessage(message, wfile)
            if not wfile.closed:
                try: wfile.flush()
                except socket.error: pass
            wfile.close()
        else:
            raise Exception('Unsupported transport: %s' % self.__transport)

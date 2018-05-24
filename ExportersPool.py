import copy
from Lib.ParameterChecking import checkType, checkIPv4, checkPort, checkOptions,\
    checkInteger, checkFloat
from Session import Session
from Exporter import Exporter

class ExportersPool(object):
    def __init__(self):
        self.__configTemplate = None
        self.__exporters = {}
        self.__configured = False
        self.__running = False
    
    def __del__(self):
        self.stop()
    
    @staticmethod
    def checkConfiguration(config):
        checkType('config', (dict,), config)

        if(('localIP' in config) and (config['localIP'] is not None)):
            checkIPv4('localIP', config['localIP'])

        if(('serverIP' in config) and (config['serverIP'] is not None)):
            checkIPv4('serverIP', config['serverIP'])

        if(('serverPort' in config) and (config['serverPort'] is not None)):
            checkPort('serverPort', config['serverPort'])

        if(('transport' in config) and (config['transport'] is not None)):
            checkOptions('transport', config['transport'], ['udp', 'tcp'])
            if(config['transport'] != 'udp'): raise Exception('Transport(%s) not implemented' % str(config['transport']))

        if(('templateRefreshTimeout' in config) and (config['templateRefreshTimeout'] is not None)):
            checkFloat('templateRefreshTimeout', config['templateRefreshTimeout'], 1, 86400)

    def configure(self, config):
        if(self.__configured): return
        ExportersPool.checkConfiguration(config)
        self.__configTemplate = config
        self.__configured = True

    def start(self):
        if(not self.__configured): return
        if(self.__running): return
        self.__running = True

    def stop(self):
        if(not self.__running): return
        for exporterId in self.__exporters.keys():
            self.remove(exporterId)
        self.__running = False
    
    def has(self, exporterId):
        checkInteger('exporterId', exporterId, 0)
        return(exporterId in self.__exporters)

    def add(self, exporterId, serverIP, serverPort):
        checkInteger('exporterId', exporterId, 0)
        checkIPv4('serverIP', serverIP)
        checkPort('serverPort', serverPort)
        if(exporterId in self.__exporters): raise Exception('Exporter(%d) already exists' % (exporterId))
        exporterConfig = copy.deepcopy(self.__configTemplate)
        exporterConfig.update({'serverIP': serverIP, 'serverPort':serverPort})
        
        session = Session()
        exporter = Exporter(session)
        exporter.configure(exporterConfig)
        exporter.start()
        self.__exporters[exporterId] = exporter

    def addDomainId(self, exporterId, obsDomainId):
        checkInteger('exporterId', exporterId, 0)
        checkInteger('obsDomainId', obsDomainId, 0)
        exporter = self.__exporters.get(exporterId, None)
        if(exporter is None): raise Exception('Exporter(%d) does not exist' % (exporterId))
        session = exporter.getSession()
        session.getDomain(obsDomainId)
    
    def addTemplate(self, exporterId, obsDomainId, template):
        checkInteger('exporterId', exporterId, 0)
        checkInteger('obsDomainId', obsDomainId, 0)
        exporter = self.__exporters.get(exporterId, None)
        if(exporter is None): raise Exception('Exporter(%d) does not exist' % (exporterId))
        session = exporter.getSession()
        if(not session.hasDomain(obsDomainId)): raise Exception('Exporter(%d) does not has domain(%d)' % (exporterId, obsDomainId))
        domain = session.getDomain(obsDomainId)
        domain.updateExporterTemplate(template)

    def get(self, exporterId):
        checkInteger('exporterId', exporterId, 0)
        exporter = self.__exporters.get(exporterId, None)
        if(exporter is None): raise Exception('Exporter(%d) does not exist' % (exporterId))
        return(exporter)

    def remove(self, exporterId):
        checkInteger('exporterId', exporterId, 0)
        if(exporterId not in self.__exporters): raise Exception('Exporter(%d) does not exist' % (exporterId))
        del self.__exporters[exporterId]

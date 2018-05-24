# Reference: https://tools.ietf.org/html/rfc7011
# Message Format:
# +----------------------------------------------------+
# | Message Header                                     |
# +----------------------------------------------------+
# | Set                                                |
# +----------------------------------------------------+
# | Set                                                |
# +----------------------------------------------------+
#   ...
# +----------------------------------------------------+
# | Set                                                |
# +----------------------------------------------------+
#
# Message Header Format:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |       Version Number          |            Length             |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                           Export Time                         |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                       Sequence Number                         |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                    Observation Domain ID                      |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import json, struct, time, calendar
from Lib.ParameterChecking import checkType
from Constants import IPFIX_VERSION
from Set import Set

class Message():
    _str = struct.Struct('!HHIII')
    
    def __init__(self):
        self.version = None
        self.length = None
        self.session = None
        self.exportTimeUTC = None
        self.sequenceNumber = None
        self.observationDomainId = None
        self.allSets = []
        self.templateSets = []
        self.optionTemplateSets = []
        self.dataSets = []
        self.dataSetIds = {}
    
    def __del__(self):
        for d in self.templateSets: del d
        for d in self.optionTemplateSets: del d
        for d in self.dataSets: del d
        
        while(len(self.dataSetIds) > 0):
            dataSetId = self.dataSetIds.keys()[0]
            del self.dataSetIds[dataSetId]

        del self.version
        del self.length
        del self.session
        del self.exportTimeUTC
        del self.sequenceNumber
        del self.observationDomainId
        del self.allSets
        del self.templateSets
        del self.optionTemplateSets
        del self.dataSets
        del self.dataSetIds

    @classmethod
    def create(cls, session, observationDomainId, explicitTimeStamp=None, version=IPFIX_VERSION):
        from Session import Session
        checkType('session', (Session,), session)
        if(explicitTimeStamp is not None):
            checkType('explicitTimeStamp', (int, long, float), explicitTimeStamp)
        
        msg = cls()
        msg.session = session
        msg.exportTimeUTC = time.gmtime(explicitTimeStamp)
        msg.version = version
        msg.observationDomainId = observationDomainId
        return(msg)
    
    @classmethod
    def _readHeader(cls, rawData, message):
        data = rawData.read(Message._str.size)
        (version, length, exportTimeUTC, sequenceNumber, observationDomainId) = Message._str.unpack_from(data)
        
        if(version != IPFIX_VERSION): raise Exception('Invalid message version')
        if(length == 0): raise Exception('Invalid message length')
        exportTimeUTC = time.gmtime(exportTimeUTC)
        domain = message.session.getDomain(observationDomainId)
        domain.getCollectorSequentiation().check(sequenceNumber, exportTimeUTC)
        message.version = version
        message.length = length
        message.exportTimeUTC = exportTimeUTC
        message.sequenceNumber = sequenceNumber
        message.observationDomainId = observationDomainId

    @classmethod
    def read(cls, session, rawData):
        from Session import Session
        checkType('session', (Session,), session)
        msg = cls()
        msg.session = session
        Message._readHeader(rawData, msg)
        domain = msg.session.getDomain(msg.observationDomainId)
        while(rawData.tell() < msg.length):
            set_ = Set.read(domain, rawData)
            if(set_.setId == 2):
                msg.templateSets.append(set_)
                msg.allSets.append(set_)
            elif(set_.setId == 3):
                msg.optionTemplateSets.append(set_)
                msg.allSets.append(set_)
            else:
                msg.dataSets.append(set_)
                msg.allSets.append(set_)

        sequentiation = domain.getCollectorSequentiation()
        _, _ = sequentiation.get()
        numDataRecords = msg.getNumDataRecords()
        sequentiation.update(numDataRecords, msg.exportTimeUTC)
        return(msg)
    
    def getObservationDomainId(self): return(self.observationDomainId)
    def getExportTimeUTC(self): return(self.exportTimeUTC)

    def _computeLength(self):
        self.length = Message._str.size
        for set_ in self.allSets:
            self.length += set_._computeLength()
    
    def _writeHeader(self, rawData):
        rawData.write(Message._str.pack(self.version, self.length, calendar.timegm(self.exportTimeUTC),
                                        self.sequenceNumber, self.observationDomainId))
    
    def write(self, rawData):
        if(self.sequenceNumber is None):
            domain = self.session.getDomain(self.observationDomainId)
            sequentiation = domain.getExporterSequentiation()
            nextSequenceNumber, _ = sequentiation.get()
            self.sequenceNumber = nextSequenceNumber
            if(self.exportTimeUTC is None): self.exportTimeUTC = time.gmtime()
            numDataRecords = self.getNumDataRecords()
            sequentiation.update(numDataRecords, self.exportTimeUTC)

        self._computeLength()
        self._writeHeader(rawData)
        for set_ in self.allSets:
            set_.write(rawData)
    
    def getNumDataRecords(self):
        numDataRecords = 0
        for dataSet in self.dataSets:
            numDataRecords += dataSet.getNumRecords()
        return(numDataRecords)
    
    def addTemplateSet(self):
        templateSet = Set.createTemplateSet()
        self.templateSets.append(templateSet)
        self.allSets.append(templateSet)
        return(templateSet)

    def addOptionTemplateSet(self):
        optionTemplateSet = Set.createOptionTemplateSet()
        self.optionTemplateSets.append(optionTemplateSet)
        self.allSets.append(optionTemplateSet)
        return(optionTemplateSet)

    def addDataSet(self, setId):
        if(setId in self.dataSetIds): return(self.dataSetIds[setId])
        domain = self.session.getDomain(self.observationDomainId)
        dataSet = Set.createDataSet(domain, setId)
        self.dataSets.append(dataSet)
        self.allSets.append(dataSet)
        self.dataSetIds[setId] = dataSet
        return(dataSet)
    
    def toJSON(self):
        d = {
            #'version': self.version,
            #'length': self.length,
            'exportTimeUTC': calendar.timegm(self.exportTimeUTC),
            #'exportTimeUTC_str': time.strftime('%Y-%m-%d %H:%M:%S', self.exportTimeUTC),
            'sequenceNumber': self.sequenceNumber,
            'observationDomainId': self.observationDomainId
        }
        if(len(self.templateSets) > 0):
            d['templateSets'] = map(lambda s: s.toJSON(), self.templateSets)
        if(len(self.optionTemplateSets) > 0):
            d['optionTemplateSets'] = map(lambda s: s.toJSON(), self.optionTemplateSets),
        if(len(self.dataSets) > 0):
            d['dataSets'] = map(lambda s: s.toJSON(), self.dataSets)
        return(d)

    def __str__(self):
        return(json.dumps(self.toJSON()))

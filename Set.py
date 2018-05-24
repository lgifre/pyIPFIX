# Reference: https://tools.ietf.org/html/rfc7011
# Set Format:
# +--------------------------------------------------+
# | Set Header                                       |
# +--------------------------------------------------+
# | record                                           |
# +--------------------------------------------------+
# | record                                           |
# +--------------------------------------------------+
#  ...
# +--------------------------------------------------+
# | record                                           |
# +--------------------------------------------------+
# | Padding (opt.)                                   |
# +--------------------------------------------------+
#
# Set Header Format:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |          Set ID               |          Length               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import struct, logging, json
from Lib.ParameterChecking import checkType, checkInteger
from TemplateRecord import TemplateRecord
from OptionTemplateRecord import OptionTemplateRecord
from DataRecord import DataRecord
from ObservationDomain import ObservationDomain

class Set(object):
    _str = struct.Struct('!HH')
    
    def __init__(self):
        self.setId = None
        self.setType = None
        self.length = None
        self.padLength = None
        self.records = []
    
    def __del__(self):
        for r in self.records: del r
        del self.setId
        del self.setType
        del self.length
        del self.padLength
        del self.records

    @classmethod
    def createTemplateSet(cls):
        obj = cls()
        obj.setId = 2
        obj.setType = 'template'
        return(obj)

    @classmethod
    def createOptionTemplateSet(cls):
        obj = cls()
        obj.setId = 3
        obj.setType = 'optionTemplate'
        return(obj)
    
    @classmethod
    def createDataSet(cls, domain, setId):
        checkType('domain', (ObservationDomain,), domain)
        checkInteger('setId', setId)
        if((setId == 0) or (setId == 1)): raise Exception('Unusable SetId(%d)' % setId)
        if(setId == 2): raise Exception('SetId(%d) can only be used in TemplateSets' % setId)
        if(setId == 3): raise Exception('SetId(%d) can only be used in OptionTemplateSets' % setId)
        if((setId >= 4) and (setId <= 255)): raise Exception('Reserved SetId(%d)' % setId)
        if(not domain.hasExporterTemplate(setId)):
            raise Exception('Domain(%d) does not contain Exporter Template(%d)' % (domain.obsDomainId, setId))
        obj = cls()
        obj.setId = setId
        obj.setType = 'data'
        return(obj)
    
    @classmethod
    def _readHeader(cls, rawData, obj):
        data = rawData.read(Set._str.size)
        (setId, length) = Set._str.unpack_from(data)
        
        if((setId == 0) or (setId == 1)):
            raise Exception('Unusable Set Type (%d)' % setId)
        elif((setId >= 4) and (setId <= 255)):
            raise Exception('Reserved Set Type (%d)' % setId)
        elif(setId == 2):
            obj.setId = setId
            obj.setType = 'template'
            obj.length = length
        elif(setId == 3):
            obj.setId = setId
            obj.setType = 'optionTemplate'
            obj.length = length
        else:
            obj.setId = setId
            obj.setType = 'data'
            obj.length = length

    @classmethod
    def read(cls, domain, rawData):
        logger = logging.getLogger(__name__)

        obj = cls()
        baseOffset = rawData.tell()
        cls._readHeader(rawData, obj)
        if(obj.setType == 'template'):
            while(obj.length - (rawData.tell() - baseOffset) > 4):
                record = TemplateRecord.read(rawData)
                obj.records.append(record)
        elif(obj.setType == 'optionTemplate'):
            while(obj.length - (rawData.tell() - baseOffset) > 4):
                OptionTemplateRecord.read(rawData)
                obj.records.append(record)
        else:
            if(not domain.hasCollectorTemplate(obj.setId)):
                logger.warning('Ignoring DataRecord since ObservationDomain(%d) does not contain Collector Template(%d)' % (domain.obsDomainId, obj.setId))
                cls._readPadding(rawData, obj, baseOffset)
            else:
                template = domain.getCollectorTemplate(obj.setId)
                while(obj.length - (rawData.tell() - baseOffset) > 4):
                    record = DataRecord.read(template, rawData, domain)
                    obj.records.append(record)
        cls._readPadding(rawData, obj, baseOffset)
        return(obj)
    
    @classmethod
    def _readPadding(cls, rawData, obj, baseOffset):
        paddingSize = obj.length - (rawData.tell() - baseOffset)
        rawData.read(paddingSize)
    
    def _computeLength(self):
        self.length = Set._str.size
        for record in self.records:
            self.length += record._computeLength()
        remLength = self.length % 4
        self.padLength = 0 if(remLength == 0) else (4 - remLength)
        self.length += self.padLength
        return(self.length)

    def _writeHeader(self, rawData):
        rawData.write(Set._str.pack(self.setId, self.length))

    def _writePadding(self, rawData):
        if(self.padLength > 0):
            rawData.write(struct.pack('x'*self.padLength))
    
    def write(self, rawData):
        self._writeHeader(rawData)
        for record in self.records:
            record.write(rawData)
        self._writePadding(rawData)
    
    def addRecord(self, record):
        if(self.setType == 'template'):
            checkType('record', (TemplateRecord,), record)
        elif(self.setType == 'optionTemplate'):
            checkType('record', (OptionTemplateRecord,), record)
        elif(self.setType == 'data'):
            checkType('record', (DataRecord,), record)
        else:
            raise Exception('Invalid Set Type(%s)' % str(self.setType))
        self.records.append(record)

    def getNumRecords(self): return(len(self.records))
    def getRecords(self): return(self.records)

    def getRecord(self, index):
        checkInteger('index', index)
        maxIndex = len(self.records)-1
        if(index < 0 or index > maxIndex):
            raise Exception('Out of range index(%d) must be between 0 and length-1(%d)' % (
                            index, maxIndex))
        return(self.records[index])

    def toJSON(self):
        return({
            'setId': self.setId,
            #'setType': self.setType,
            #'length': self.length,
            #'padLength': self.padLength,
            'records': map(lambda s: s.toJSON(), self.records)
        })
    
    def __str__(self):
        return(json.dumps(self.toJSON()))

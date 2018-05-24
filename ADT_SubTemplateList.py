# Reference: https://tools.ietf.org/html/rfc6313#section-4.5.2
# subTemplateList encoding:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |   Semantic    |         Template ID           |     ...       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                subTemplateList Content    ...                 |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                              ...                              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import json, struct
from Lib.ParameterChecking import checkType, checkInteger, checkAttr
from TemplateRecord import TemplateRecord
from DataRecord import DataRecord
from ADT_Semantics import checkSemantics

class ADT_SubTemplateList(object):
    _str = struct.Struct('!BH')
    
    def __init__(self):
        self.semantic = None
        self.template = None
        self.templateId = None
        self.records = []

    def __del__(self):
        for r in self.records: del r
        del self.semantic
        del self.template
        del self.templateId
        del self.records

    @classmethod
    def create(cls, semantic, template):
        checkSemantics(semantic)
        checkType('template', (TemplateRecord,), template)
        obj = cls()
        obj.semantic = semantic
        obj.template = template
        obj.templateId = template.getId()
        return(obj)

    @classmethod
    def read(cls, rawData, length, domain):
        if(length < ADT_SubTemplateList._str.size):
            raise Exception('Insufficient data to read a FieldValue_SubTemplateList field')
        obj = cls()
        data = rawData.read(ADT_SubTemplateList._str.size)
        (obj.semantic, obj.templateId) = ADT_SubTemplateList._str.unpack_from(data)
        obj.template = domain.getCollectorTemplate(obj.templateId)
        baseOffset = rawData.tell()
        length -= ADT_SubTemplateList._str.size
        while((rawData.tell() - baseOffset) < length):
            record = DataRecord.read(obj.template, rawData, domain)
            obj.records.append(record)
        return(obj)

    @classmethod
    def fromJSON(cls, data):
        obj = cls()
        
        semantic = checkAttr('semantic', data)
        checkSemantics(semantic)
        obj.semantic = semantic

        template = checkAttr('template', data)
        template = TemplateRecord.newFromJSON(template['templateId'], template['fields'])
        checkType('template', (TemplateRecord,), template)
        obj.template = template
        obj.templateId = template.getId()
        obj.records = map(lambda x: DataRecord.create(template, x['values']), data['records'])
        return(obj)

    def getSemantic(self): return(self.semantic)
    def getTemplateId(self): return(self.templateId)
    def getTemplate(self): return(self.template)

    def addDataRecord(self, values):
        checkType('values', (dict,), values)
        self.records.append(DataRecord.create(self.template, values))

    def getNumRecords(self): return(len(self.records))
    def getRecords(self): return(self.records)

    def getRecord(self, index):
        checkInteger('index', index)
        maxIndex = len(self.records)-1
        if(index < 0 or index > maxIndex):
            raise Exception('Out of range index(%d) must be between 0 and length-1(%d)' % (
                            index, maxIndex))
        return(self.records[index])
    
    def sortRecords(self, fieldName, ascending=True):
        self.records.sort(key=lambda x: x.getField(fieldName), reverse=(not ascending))
    
    def _computeLength(self):
        length = 3 # 1 byte for semantic + 2 bytes for templateId
        for record in self.records:
            length += record._computeLength()
        return(length)

    def _writeHeader(self, rawData):
        rawData.write(ADT_SubTemplateList._str.pack(self.semantic, self.templateId))

    def write(self, rawData):
        self._writeHeader(rawData)
        for record in self.records:
            record.write(rawData)

    def toJSON(self):
        return({
            'templateId': self.templateId,
            'template': self.template.toJSON(),
            'semantic': self.semantic,
            'records': map(lambda s: s.toJSON(), self.records)
        })

    def __str__(self):
        return(json.dumps(self.toJSON()))

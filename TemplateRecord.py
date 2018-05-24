# Reference: https://tools.ietf.org/html/rfc7011
# Template Record Format:
# +--------------------------------------------------+
# | Template Record Header                           |
# +--------------------------------------------------+
# | Field Specifier                                  |
# +--------------------------------------------------+
# | Field Specifier                                  |
# +--------------------------------------------------+
#  ...
# +--------------------------------------------------+
# | Field Specifier                                  |
# +--------------------------------------------------+
#
# Template Record Header Format:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |      Template ID (> 255)      |         Field Count           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import struct, json
from Lib.ParameterChecking import checkInteger, checkType
from FieldSpecifier import FieldSpecifier

class TemplateRecord(object):
    _str = struct.Struct('!HH')
    
    def __init__(self):
        self.templateId = None
        self.fieldCount = 0
        self.fields = []
    
    @classmethod
    def create(cls, templateId, fields):
        checkInteger('templateId', templateId, 1)
        checkType('fields', (list,), fields)
        
        for field in fields:
            checkType('field', (FieldSpecifier,), field)
        
        obj = cls()
        obj.templateId = templateId
        obj.fields = fields
        obj.fieldCount = len(obj.fields)
        return(obj)

    @staticmethod
    def checkJSON(fields):
        checkType('fields', (list,), fields)

        fields_ = []
        idValues = set()
        for field in fields:
            field_ = FieldSpecifier.newFromJSON(field)
            id_ = field_.informationElementId
            if(id_ in idValues): raise Exception('Multiple occurrences of id(%d) in template' % id_)
            idValues.add(id_)
            fields_.append(field_)
        return(fields_)

    @classmethod
    def newFromJSON(cls, templateId, fields):
        checkInteger('templateId', templateId, 1)
        fields_ = TemplateRecord.checkJSON(fields)
        return(TemplateRecord.create(templateId, fields_))

    @classmethod
    def read(cls, rawData):
        obj = cls()
        cls._readHeader(rawData, obj)
        for _ in xrange(0, obj.fieldCount):
            field = FieldSpecifier.read(rawData)
            obj.fields.append(field)
        return(obj)
    
    @classmethod
    def _readHeader(cls, rawData, obj):
        data = rawData.read(TemplateRecord._str.size)
        (templateId, fieldCount) = TemplateRecord._str.unpack_from(data)
        
        if((templateId < 256) or (templateId > 65535)): raise Exception('Template Id (%d) out of range' % (templateId))
        if(fieldCount == 0): raise Exception('Template Id (%d) has no fields' % (templateId))
        
        obj.templateId = templateId
        obj.fieldCount = fieldCount
    
    def _computeLength(self):
        length = TemplateRecord._str.size
        for field in self.fields: length += field._computeLength()
        return(length)

    def getId(self):        return(self.templateId)
    def getLength(self):    return(self._computeLength())
    def getNumFields(self): return(self.fieldCount)
    
    def getField(self, index):
        checkInteger('index', index, 0, self.fieldCount)
        return(self.fields[index])
    
    def _writeHeader(self, rawData):
        rawData.write(TemplateRecord._str.pack(self.templateId, self.fieldCount))
    
    def write(self, rawData):
        self._writeHeader(rawData)
        for field in self.fields:
            field.write(rawData)

    def toJSON(self):
        return({
            'templateId': self.templateId,
            #'fieldCount': self.fieldCount,
            'fields': map(lambda s: s.toJSON(), self.fields)
        })
    
    def __str__(self):
        return(json.dumps(self.toJSON()))

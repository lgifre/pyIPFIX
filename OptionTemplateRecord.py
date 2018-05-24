# Reference: https://tools.ietf.org/html/rfc7011
# Options Template Record Format:
# +--------------------------------------------------+
# | Options Template Record Header                   |
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
# Options Template Record Header Format:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |      Template ID (> 255)      |         Field Count           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |      Scope Field Count        |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import struct, json
from FieldSpecifier import FieldSpecifier

class OptionTemplateRecord(object):
    _str = struct.Struct('!HHH')
    
    def __init__(self):
        self.templateId = None
        self.fieldCount = None
        self.scopeFieldCount = None
        self.fields = []
        self.scopeFields = []
    
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
        data = rawData.read(OptionTemplateRecord._str.size)
        (templateId, fieldCount, scopeFieldCount) = OptionTemplateRecord._str.unpack_from(data)
        
        if((templateId < 256) or (templateId > 65535)): raise Exception('Options Template Id (%d) out of range' % (templateId))
        if(fieldCount == 0): raise Exception('Options Template Id (%d) has no fields' % (templateId))
        if(scopeFieldCount == 0): raise Exception('Options Template Id (%d) has no scope fields' % (templateId))
        if(fieldCount < scopeFieldCount): raise Exception('Options Template Id (%d) has less fields(%d) than scope fields(%d)' % (templateId, fieldCount, scopeFieldCount))
        
        obj.templateId = templateId
        obj.fieldCount = fieldCount
        obj.scopeFieldCount = scopeFieldCount

    def _computeLength(self):
        length = OptionTemplateRecord._str.size
        for field in self.fields:
            length += field._computeLength()
        return(length)

    def _writeHeader(self, rawData):
        rawData.write(OptionTemplateRecord._str.pack(self.templateId, self.fieldCount))
    
    def write(self, rawData):
        self._writeHeader(rawData)
        for field in self.fields:
            field.write(rawData)

    def toJSON(self):
        return({
            'templateId': self.templateId,
            #'fieldCount': self.fieldCount,
            #'scopeFieldCount': self.scopeFieldCount,
            'fields': map(lambda s: s.toJSON(), self.fields),
            'scopeFields': map(lambda s: s.toJSON(), self.scopeFields)
        })
    
    def __str__(self):
        return(json.dumps(self.toJSON()))

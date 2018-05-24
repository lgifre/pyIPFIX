# Reference: https://tools.ietf.org/html/rfc6313#section-4.5.1
# basicList encoding for an IANA field:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |   Semantic    |0|          Field ID           |   Element...  |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# | ...Length     |           basicList Content ...               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                              ...                              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                              ...                              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
# basicList encoding for a private field:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |    Semantic   |1|         Field ID            |   Element...  |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# | ...Length     |               Enterprise Number ...           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |      ...      |              basicList Content ...            |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                              ...                              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import struct, json
from Lib.ParameterChecking import checkType, checkInteger
from FieldSpecifier import FieldSpecifier
from DataRecord import DataRecord
from ADT_Semantics import checkSemantics
from FieldValue import FieldValue

class ADT_BasicList(object):
    _strSemantic = struct.Struct('!B')

    def __init__(self):
        self.semantic = None
        self.field = None
        self.fieldId = None
        self.values = []

    def __del__(self):
        for v in self.values: del v
        del self.semantic
        del self.field
        del self.fieldId
        del self.values

    @classmethod
    def create(cls, semantic, field):
        checkSemantics(semantic)
        checkType('field', (FieldSpecifier,), field)
        obj = cls()
        obj.semantic = semantic
        obj.field = field
        obj.fieldId = field.getId()
        return(obj)

    @classmethod
    def read(cls, rawData, length, domain):
        baseOffset = rawData.tell()
        if(length < ADT_BasicList._strSemantic.size):
            raise Exception('Insufficient data to read semantic field of a BasicList')
        data = rawData.read(ADT_BasicList._strSemantic.size)
        obj = cls()
        (obj.semantic,) = ADT_BasicList._strSemantic.unpack_from(data)
        obj.field = FieldSpecifier.read(rawData)
        obj.fieldId = obj.field.getId()
        
        length -= (rawData.tell() - baseOffset + 1)
        baseOffset = rawData.tell()
        while((rawData.tell() - baseOffset) < length):
            value = FieldValue.read(obj.field, rawData, domain)
            obj.values.append(value)
        return(obj)
    
    def getSemantic(self): return(self.semantic)
    def getFieldId(self): return(self.fieldId)
    def getField(self): return(self.field)

    def addValue(self, value):
        recordLength = [0]
        self.values.append(FieldValue.create(self.field, value, recordLength))

    def getNumValues(self): return(len(self.values))
    def getValues(self): return(self.values)

    def getValue(self, index):
        checkInteger('index', index)
        maxIndex = len(self.values)-1
        if(index < 0 or index > maxIndex):
            raise Exception('Out of range index(%d) must be between 0 and length-1(%d)' % (
                            index, maxIndex))
        return(self.values[index])
    
    def _computeLength(self):
        length = 5 # 1 byte for semantic + 2 bytes for fieldId + 2 bytes for field length
        if(self.field.isEnterprise()): length += 4 # enterprise number
        for value in self.values:
            length += value._computeLength()
        return(length)

    def _writeHeader(self, rawData):
        rawData.write(ADT_BasicList._strSemantic.pack(self.semantic))
        self.field.write(rawData)

    def write(self, rawData):
        self._writeHeader(rawData)
        for value in self.values:
            value.write(rawData)

    def toJSON(self):
        d = {
            'fieldId': self.fieldId,
            'values': map(lambda s: s.toJSON(), self.values)
        }
        if(self.field.isEnterprise()): d['pen'] = self.field.getEnterpriseNumber()
        return(d)

    def __str__(self):
        return(json.dumps(self.toJSON()))

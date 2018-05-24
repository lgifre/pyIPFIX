# Reference: https://tools.ietf.org/html/rfc7011
# Field Specifier Format:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |E|  Information Element ident. |        Field Length           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                      Enterprise Number                        |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

import struct, logging, json
from Constants import VARIABLE_LENGTH, TypeBasicList, TypeSubTemplateList, \
                      getIANAFieldByName, getIANAFieldById, validatePEN, \
                      getPENFieldById, getPENFieldByName, getStructForType, \
                      getReducedType
from Lib.ParameterChecking import checkAttr, checkInteger

class FieldSpecifier(object):
    _strCommon = struct.Struct('!HH')
    _strEntNum = struct.Struct('!I')
    
    def __init__(self):
        self.enterprise = None
        self.informationElementId = None
        self.name = None
        self.type = None
        self.struct_ = None
        self.minValue = None
        self.maxValue = None
        self.choose = None
        self.length = None
        self.variableLength = None
        self.enterpriseNumber = None
    
    def getId(self): return(self.informationElementId)
    def getName(self): return(self.name)
    def isEnterprise(self): return(self.enterprise)
    def getEnterpriseNumber(self): return(self.enterpriseNumber)
    def isVariableLength(self): return(self.variableLength)
    def getLength(self): return(self.length)
    
    @classmethod
    def _reducePattern(cls, field):
        if(field.struct_ is None): return
        if(field.length == field.struct_.size): return
        if(field.variableLength): return
        try:
            reducedType = getReducedType(field.type, field.length)
            field.struct_ = getStructForType(reducedType, field.name)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.debug('Exception Reducing Field: name(%s) type(%s) length(%s)' % (
                field.name, field.type, field.length))
            logger.exception(e)
    
    @classmethod
    def _validateCommon(cls, obj):
        if(obj.length is not None):
            if(obj.length == 0): raise Exception('Invalid Field Length of zero')
            obj.variableLength = (obj.length == VARIABLE_LENGTH)
    
    @classmethod
    def _validateFieldAttr(cls, obj, field):
        obj.name = field['name']
        obj.type = field['type']
        obj.struct_ = getStructForType(obj.type, obj.name, obj.length)
        if(not obj.variableLength):
            #obj.struct_ = getStructForType(obj.type, obj.name, obj.length)
            if(isinstance(obj.struct_, (struct.Struct,))):
                if(obj.length is None):
                    obj.length = obj.struct_.size
            elif(isinstance(obj.struct_, (TypeBasicList, TypeSubTemplateList))):
                pass
            else:
                raise Exception('Unknown FieldType(%s)' % str(obj.struct_)) 
        
        if(isinstance(obj.struct_, (TypeBasicList, TypeSubTemplateList))):
            obj.length = VARIABLE_LENGTH
            obj.variableLength = True
        else:
            cls._reducePattern(obj)
            obj.minValue = field['minValue'] if(field.has_key('minValue')) else None
            obj.maxValue = field['maxValue'] if(field.has_key('maxValue')) else None
            obj.choose = field['choose'] if(field.has_key('choose')) else None
    
    @classmethod
    def _validateIANA(cls, obj):
        field = None
        if(isinstance(obj.informationElementId, (basestring, str))):
            field = getIANAFieldByName(obj.informationElementId)
        elif(isinstance(obj.informationElementId, (int, long,))):
            field = getIANAFieldById(obj.informationElementId)
        else:
            raise Exception('Invalid informationElementId(%s)' % str(obj.informationElementId))
        obj.informationElementId = field[0]
        cls._validateFieldAttr(obj, field[1])

    @classmethod
    def _validateEnterprise(cls, obj):
        validatePEN(obj.enterpriseNumber)
        field = None
        if(isinstance(obj.informationElementId, (basestring, str))):
            field = getPENFieldByName(obj.informationElementId, obj.enterpriseNumber)
        elif(isinstance(obj.informationElementId, (int, long,))):
            field = getPENFieldById(obj.informationElementId, obj.enterpriseNumber)
        else:
            raise Exception('Invalid informationElementId(%s) for PEN(%s)' % (str(obj.informationElementId), str(obj.enterpriseNumber)))
        obj.informationElementId = field[0]
        cls._validateFieldAttr(obj, field[1])
    
    @classmethod
    def newIANA(cls, informationElementId, length=None):
        obj = cls()
        obj.enterprise = False
        obj.informationElementId = informationElementId
        obj.length = length
        cls._validateCommon(obj)
        cls._validateIANA(obj)
        return(obj)
    
    @classmethod
    def newEnterprise(cls, informationElementId, enterpriseNumber, length=None):
        obj = cls()
        obj.enterprise = True
        obj.enterpriseNumber = enterpriseNumber
        obj.informationElementId = informationElementId
        obj.length = length
        cls._validateCommon(obj)
        cls._validateEnterprise(obj)
        return(obj)
    
    @staticmethod
    def checkJSON(field):
        id_ = checkAttr('id', field)
        checkInteger('id', id_, 1, 2**15-1)
            
        pen = None
        if('pen' in field):
            pen = checkAttr('pen', field)
            checkInteger('pen', pen, 1, 2**32-1)
            
        name = checkAttr('name', field)
        fieldInfo = getIANAFieldById(id_) if(pen is None) else getPENFieldById(id_, pen)
        fieldName = fieldInfo[1]['name']
        if(name != fieldName): raise Exception('Field name(%s) does not match id(%d)' % (name, id_))
            
        length = None
        if('length' in field):
            length = checkAttr('length', field)
            checkInteger('length', length, 1)

        type_ = checkAttr('type', field)
        getStructForType(ie_type=type_, fieldName=name, length=length)
        
        return(id_, pen, name, length, type_)

    @classmethod
    def newFromJSON(cls, field):
        id_, pen, _, length, _ = FieldSpecifier.checkJSON(field)
        
        obj = cls()
        obj.enterprise = (pen is not None)
        obj.enterpriseNumber = pen
        obj.informationElementId = id_
        obj.length = length
        cls._validateCommon(obj)
        if(obj.enterprise):
            cls._validateEnterprise(obj)
        else:
            cls._validateIANA(obj)
        return(obj)

    @classmethod
    def read(cls, rawData):
        obj = cls()
        data = rawData.read(FieldSpecifier._strCommon.size)
        (obj.informationElementId, obj.length) = FieldSpecifier._strCommon.unpack_from(data)
        cls._validateCommon(obj)
        obj.enterprise = (obj.informationElementId & 0x08000 != 0)
        if(obj.enterprise):
            obj.informationElementId -= 0x08000
            data = rawData.read(FieldSpecifier._strEntNum.size)
            (obj.enterpriseNumber,) = FieldSpecifier._strEntNum.unpack_from(data)
            cls._validateEnterprise(obj)
        else:
            cls._validateIANA(obj)
        return(obj)

    def _computeLength(self):
        length = FieldSpecifier._strCommon.size
        if(self.enterprise): length += FieldSpecifier._strEntNum.size
        return(length)

    def write(self, rawData):
        informationElementId = self.informationElementId
        if(self.enterprise): informationElementId += 0x08000
        rawData.write(FieldSpecifier._strCommon.pack(informationElementId, self.length))
        if(self.enterprise): rawData.write(FieldSpecifier._strEntNum.pack(self.enterpriseNumber))

    def toJSON(self):
        d = {
             'id': self.informationElementId,
             'name': self.name,
             'type': self.type,
             'length': self.length
        }
        if(self.enterprise): d['pen'] = self.enterpriseNumber
        return(d)
    
    def __str__(self):
        return(json.dumps(self.toJSON()))

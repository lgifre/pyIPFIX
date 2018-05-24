# Reference: https://tools.ietf.org/html/rfc7011
# Format depends on field

import struct, logging, binascii, json
from Lib.ParameterChecking import checkType
from FieldSpecifier import FieldSpecifier
from Constants import getStructForType, TypeBasicList, TypeSubTemplateList

class FieldValue(object):
    _strShortLength = struct.Struct('!B')
    _strLongLength = struct.Struct('!H')
    
    def __init__(self):
        self.field = None
        self.struct_ = None
        self.length = None
        self.value = None

    def __del__(self):
        del self.field
        del self.struct_
        del self.length
        del self.value

    @classmethod
    def create(cls, field, value, recordLength):
        checkType('field', (FieldSpecifier,), field)
        
        length = None
        struct_ = field.struct_
        if(field.variableLength):
            if(isinstance(struct_, (TypeBasicList, TypeSubTemplateList))):
                length = value._computeLength()
            else:
                length = len(value)
            if(length > 65535): raise Exception('Maximum length(65535) exceeded: %d' % length)
            struct_ = getStructForType(field.type, field.name, length=length)
        
        if(struct_ is None):
            raise Exception('Undefined struct for FieldSpecifier(%s)' % field.name)
        
        if(field.variableLength):
            if(isinstance(struct_, (TypeBasicList, TypeSubTemplateList))):
                recordLength[0] += length + (3 if(length > 254) else 1)
            else:
                recordLength[0] += struct_.size + (3 if(struct_.size > 254) else 1)
        else:
            recordLength[0] += struct_.size
        
        obj = cls()
        obj.field = field
        obj.struct_ = struct_
        obj.length = length
        obj.value = value
        
        if(not isinstance(struct_, (TypeBasicList, TypeSubTemplateList))):
            if((field.minValue is not None) and (obj.value < field.minValue)): raise Exception('Underflow value(%s) < minValue(%s) in field(%s)' % (str(obj.value), str(field.minValue), field.name))
            if((field.maxValue is not None) and (obj.value > field.maxValue)): raise Exception('Overflow value(%s) > maxValue(%s) in field(%s)' % (str(obj.value), str(field.minValue), field.name))
            if((field.choose is not None) and (obj.value not in field.choose)): raise Exception('Invalid choice(%s) in field(%s)' % (str(obj.value), field.name))
        return(obj)
    
    @classmethod
    def read(cls, field, rawData, domain):
        checkType('field', (FieldSpecifier,), field)
        
        obj = cls()
        obj.field = field
        
        length = None
        struct_ = None
        if(field.variableLength):
            data = rawData.read(1)
            length = FieldValue._strShortLength.unpack_from(data)[0]
            if(length == 255):
                data = rawData.read(2)
                length = FieldValue._strLongLength.unpack_from(data)[0]
            struct_ = getStructForType(field.type, field.name, length=length)
        else:
            if(field.struct_ is None):
                raise Exception('Undefined struct for FieldSpecifier(%s)' % field.name)
            struct_ = obj.field.struct_
            length = struct_.size
        data = None
        try:
            if(isinstance(struct_, (TypeBasicList,))):
                from ADT_BasicList import ADT_BasicList
                obj.value = ADT_BasicList.read(rawData, length, domain)
            elif(isinstance(struct_, (TypeSubTemplateList,))):
                from ADT_SubTemplateList import ADT_SubTemplateList
                obj.value = ADT_SubTemplateList.read(rawData, length, domain)
            else:
                data = rawData.read(length)
                obj.value = struct_.unpack_from(data)
                if(isinstance(obj.value, (tuple,))):
                    if(obj.field.type=='string'):
                        obj.value = ''.join(map(str, obj.value)) # convert chars to string
                        obj.value = obj.value.strip() # remove leading and tailing whitespaces
                    elif(obj.field.type=='octetArray'):
                        obj.value = ''.join(map(chr, obj.value)) # convert ascii values to string
        except Exception as e:
            logger = logging.getLogger(__name__)
            if(field.variableLength):
                logger.error('Error reading field(%s) with struct(%s) length(%d) rawData(%s)' % (
                                obj.field.name,
                                struct_.format if(struct_ is not None) else None,
                                struct_.size if(struct_ is not None) else length,
                                binascii.hexlify(data) if(data is not None) else data))
            else:
                logger.error('Error reading field(%s) with struct(%s) length(%d) rawData(%s)' % (
                                obj.field.name,
                                obj.field.struct_.format,
                                obj.field.struct_.size,
                                binascii.hexlify(data)))
            logger.exception(e)

        if(not isinstance(struct_, (TypeBasicList, TypeSubTemplateList))):
            if(len(obj.value) == 1): obj.value = obj.value[0]
            if((field.minValue is not None) and (obj.value < field.minValue)): raise Exception('Underflow value(%s) < minValue(%s) in field(%s)' % (str(obj.value), str(field.minValue), field.name))
            if((field.maxValue is not None) and (obj.value > field.maxValue)): raise Exception('Overflow value(%s) > maxValue(%s) in field(%s)' % (str(obj.value), str(field.minValue), field.name))
            if((field.choose is not None) and (obj.value not in field.choose)): raise Exception('Invalid choice(%s) in field(%s)' % (str(obj.value), field.name))
        return(obj)
    
    def _computeLength(self):
        if(self.field.variableLength):
            extra = 1 if(self.length < 255) else 3
            return(self.length + extra)
        else:
            return(self.field.struct_.size)

    def write(self, rawData):
        try:
            if(self.value is None): self.value = 0
            if(self.field.variableLength):
                from ADT_BasicList import ADT_BasicList
                from ADT_SubTemplateList import ADT_SubTemplateList
                if(isinstance(self.value, (str, basestring, unicode))):
                    if(self.field.type not in ['string', 'octetArray']):
                        raise Exception('Invalid field type(%s). Should be one of %s' % (str(type(self.value)), str(('string', 'octetArray'))))
                    self.length = len(self.value)
                elif(isinstance(self.value, (ADT_BasicList,))):
                    if(self.field.type not in ['basicList']):
                        raise Exception('Invalid field type(%s). Should be one of %s' % (str(type(self.value)), str(('basicList',))))
                elif(isinstance(self.value, (ADT_SubTemplateList,))):
                    if(self.field.type not in ['subTemplateList']):
                        raise Exception('Invalid field type(%s). Should be one of %s' % (str(type(self.value)), str(('subTemplateList',))))
                else:
                    raise Exception('Invalid value type(%s). Should be one of %s' % (str(type(self.value)), str((str, basestring, unicode, ADT_BasicList, ADT_SubTemplateList))))

                if(self.length < 255):
                    rawData.write(FieldValue._strShortLength.pack(self.length))
                else:
                    rawData.write(FieldValue._strShortLength.pack(255))
                    rawData.write(FieldValue._strLongLength.pack(self.length))

                if(self.field.type == 'string'):
                    self.value = tuple(str(self.value)) # convert string to char values
                    struct_ = getStructForType(self.field.type, self.field.name, self.length)
                    rawData.write(struct_.pack(*self.value))
                elif(self.field.type == 'octetArray'):
                    self.value = tuple(map(ord, tuple(self.value))) # convert string to ascii values
                    struct_ = getStructForType(self.field.type, self.field.name, self.length)
                    rawData.write(struct_.pack(*self.value))
                elif(self.field.type in ['basicList', 'subTemplateList']):
                    self.value.write(rawData)

            else:
                if(isinstance(self.value, (str, basestring, unicode))):
                    self.length = len(self.value)
                    if(self.field.type=='string'):
                        if(self.field.struct_.size > self.length):
                            self.value = self.value + ' ' * (self.field.struct_.size - self.length)
                        elif(self.field.struct_.size < self.length):
                            self.value = self.value[:self.field.struct_.size]
                        self.value = tuple(str(self.value)) # convert string to char values
                        #self.value = tuple('{:\0<16}'.format(self.value[:16]))
                    elif(self.field.type=='octetArray'):
                        self.value = tuple(map(ord, tuple(self.value))) # convert string to ascii values
                if(isinstance(self.value, (tuple, list))):
                    rawData.write(self.field.struct_.pack(*self.value))
                else:
                    rawData.write(self.field.struct_.pack(self.value))
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error('Error writing field(%s) with struct(%s) length(%d) rawData(%s)' % (
                            self.field.name,
                            self.field.struct_.format,
                            self.field.struct_.size,
                            str(self.value)))
            logger.exception(e)

    def toJSON(self, standalone=True):
        if(standalone):
            if(self.field.type == 'octetArray'):
                return({ self.field.name: 'hex<%s>' % binascii.hexlify(self.value) })
            elif(self.field.type in ['basicList', 'subTemplateList']):
                return({ self.field.name: self.value.toJSON() })
            return({ self.field.name: self.value })
        else:
            if(self.field.type == 'octetArray'):
                return('hex<%s>' % binascii.hexlify(self.value))
            elif(self.field.type in ['basicList', 'subTemplateList']):
                return(self.value.toJSON())
            return(self.value)

    def __str__(self):
        return(json.dumps(self.toJSON()))

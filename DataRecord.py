# Reference: https://tools.ietf.org/html/rfc7011
# Data Record Format:
# +--------------------------------------------------+
# | Field Value                                      |
# +--------------------------------------------------+
# | Field Value                                      |
# +--------------------------------------------------+
#  ...
# +--------------------------------------------------+
# | Field Value                                      |
# +--------------------------------------------------+

import json, copy
from Lib.ParameterChecking import checkType
from TemplateRecord import TemplateRecord
from FieldValue import FieldValue

class DataRecord(object):
    def __init__(self):
        self.templateId = None
        self.values = []
    
    def __del__(self):
        for v in self.values: del v
        del self.templateId
        del self.values
    
    @classmethod
    def create(cls, template, values):
        checkType('template', (TemplateRecord,), template)
        checkType('values', (dict,), values)
        
        obj = cls()
        obj.templateId = template.getId()
        
        padIndex = None
        recordLength = [0]
        for i in xrange(len(template.fields)):
            field = template.fields[i]
            fName = field.name
            value = None
            if(fName == 'paddingOctets'):
                if(values.has_key(fName)):
                    raise Exception('Do not provide value for field "paddingOctets". It is filled automatically, when present.')
                value = None
                padIndex = i
            else:
                if(not values.has_key(fName)):
                    raise Exception('No value provided for field(%s)' % str(fName))
                value = FieldValue.create(field, values[fName], recordLength)
            obj.values.append(value)
        
        if(padIndex is not None):
            padLength = ((recordLength[0] + 1) % 4)
            if(padLength > 0): padLength = 4 - padLength
            obj.values[padIndex] = FieldValue.create(template.fields[i], '\0'*padLength, recordLength)
            if((recordLength[0] % 4) != 0): raise Exception('Error computing padding')

        return(obj)
    
    @classmethod
    def read(cls, template, rawData, domain):
        obj = cls()
        obj.templateId = template.getId()
        for field in template.fields:
            value = FieldValue.read(field, rawData, domain)
            if(field.name == 'paddingOctets'): continue
            obj.values.append(value)
        return(obj)

    def _computeLength(self):
        length = 0
        for value in self.values:
            length += value._computeLength()
        return(length)
    
    def getTemplateId(self): return(self.templateId)
    
    def getField(self, fieldName):
        for value in self.values:
            if(fieldName == value.field.name):
                return(copy.deepcopy(value.value))
        raise Exception('Field(%s) not found' % fieldName)

    def getFieldsAsDict(self):
        fields = {}
        for value in self.values:
            name = copy.deepcopy(value.field.name)
            fields[name] = copy.deepcopy(value.value)
        return(fields)

    def write(self, rawData):
        for value in self.values:
            value.write(rawData)

    def toJSON(self):
        d = {
            'templateId': self.templateId,
            'values': {}
        }
        for value in self.values:
            if(value.field.type in ['basicList', 'subTemplateList']):
                d['values'][value.field.name] = value.toJSON()
            else:
                #d['values'][value.field.name] = value.toJSON(standalone=False)
                d['values'][value.field.name] = value.value
        return(d)
    
    def __str__(self):
        return(json.dumps(self.toJSON()))

import netaddr
from Lib.ParameterChecking import checkInteger, checkMACAddr, checkOptions,\
    checkString, checkFloat, checkIPv4
from ADT_SubTemplateList import ADT_SubTemplateList
from ADT_Semantics import parseSemantics
from Shared.Checkers import chkTemplateId

__FIELD_PARSERS = {
    'timeStamp':                    lambda v: int(float(v)),
    'name':                         lambda v: str(v),
    'containerName':                lambda v: str(v),
    'observationDomainId':          lambda v: int(v),
    'observationPointId':           lambda v: long(v),
    'flowDirection':                lambda v: str(v),
    'sourceMacAddress':             lambda v: str(v),
    'destinationMacAddress':        lambda v: str(v),
    'ethernetType':                 lambda v: str(v),
    'ethernetHeaderLength':         lambda v: int(v),
    'flowStartDeltaMicroseconds':   lambda v: int(v),
    'flowEndDeltaMicroseconds':     lambda v: int(v),
    'flowEndReason':                lambda v: int(v),
    'packetDeltaCount':             lambda v: int(v),
    'layer2OctetDeltaCount':        lambda v: int(v),
    'bitCount':                     lambda v: int(v),
    'tunnelSourceIPv4Address':      lambda v: str(v),
    'tunnelDestinationIPv4Address': lambda v: str(v),
    'direction':                    lambda v: str(v),
    'ber':                          lambda v: float(v),
    'rxPowerMilliwatts':            lambda v: float(v),
    'txPowerMilliwatts':            lambda v: float(v),
    'rxPowerDecibelMilliwatts':     lambda v: float(v),
    'txPowerDecibelMilliwatts':     lambda v: float(v),
    'frequencyGigaHertz':           lambda v: float(v),
    'stlPaginationIndex':           lambda v: int(v),
    'stlPaginationTotal':           lambda v: int(v),
}

__FIELD_CHECKERS = {
    'timeStamp':                    lambda v: checkInteger('timeStamp', v, 0),
    'name':                         lambda v: checkString('name', v),
    'containerName':                lambda v: checkString('containerName', v),
    'observationDomainId':          lambda v: checkInteger('observationDomainId', v, 0, 4294967295),
    'observationPointId':           lambda v: checkInteger('observationPointId', v, 0),
    'flowDirection':                lambda v: checkOptions('flowDirection', v, ['ingress', 'egress']),
    'sourceMacAddress':             lambda v: checkMACAddr('sourceMacAddress', v),
    'destinationMacAddress':        lambda v: checkMACAddr('destinationMacAddress', v),
    'ethernetType':                 lambda v: checkOptions('ethernetType', v, ['ARP', 'IPv4', 'IPv6', 'MPLS']),
    'ethernetHeaderLength':         lambda v: checkInteger('ethernetHeaderLength', v, 0, 0xFF),
    'flowStartDeltaMicroseconds':   lambda v: checkInteger('flowStartDeltaMicroseconds', v, 0),
    'flowEndDeltaMicroseconds':     lambda v: checkInteger('flowEndDeltaMicroseconds', v, 0),
    'flowEndReason':                lambda v: checkInteger('flowEndReason', v, 0, 5),
    'packetDeltaCount':             lambda v: checkInteger('packetDeltaCount', v, 0),
    'layer2OctetDeltaCount':        lambda v: checkInteger('layer2OctetDeltaCount', v, 0),
    'bitCount':                     lambda v: checkInteger('bitCount', v, 0),
    'tunnelSourceIPv4Address':      lambda v: checkIPv4('tunnelSourceIPv4Address', v),
    'tunnelDestinationIPv4Address': lambda v: checkIPv4('tunnelDestinationIPv4Address', v),
    'direction':                    lambda v: checkOptions('direction', v, ['ingress', 'egress', 'bidirectional']),
    'ber':                          lambda v: checkFloat('ber', v, 0),
    'rxPowerMilliwatts':            lambda v: checkFloat('rxPowerMilliwatts', v, 0),
    'txPowerMilliwatts':            lambda v: checkFloat('txPowerMilliwatts', v, 0),
    'rxPowerDecibelMilliwatts':     lambda v: checkFloat('rxPowerDecibelMilliwatts', v),
    'txPowerDecibelMilliwatts':     lambda v: checkFloat('txPowerDecibelMilliwatts', v),
    'frequencyGigaHertz':           lambda v: checkFloat('frequencyGigaHertz', v, 0),
    'stlPaginationIndex':           lambda v: checkInteger('stlPaginationIndex', v, 0),
    'stlPaginationTotal':           lambda v: checkInteger('stlPaginationTotal', v, 0),
}

__FIELD_TRANSLATORS = {
    'timeStamp':                    lambda v: v,
    'name':                         lambda v: v,
    'containerName':                lambda v: v,
    'observationDomainId':          lambda v: v,
    'observationPointId':           lambda v: v,
    'flowDirection':                lambda v: {'ingress':0, 'egress':1}[v],
    'sourceMacAddress':             lambda v: tuple(map(lambda x: int(x, 16), v.split(':'))),
    'destinationMacAddress':        lambda v: tuple(map(lambda x: int(x, 16), v.split(':'))),
    'ethernetType':                 lambda v: {'ARP': 0x0806, 'IPv4':0x0800, 'IPv6':0x86DD, 'MPLS':0x8847}[v],
    'ethernetHeaderLength':         lambda v: v,
    'flowStartDeltaMicroseconds':   lambda v: v,
    'flowEndDeltaMicroseconds':     lambda v: v,
    'flowEndReason':                lambda v: v,
    'packetDeltaCount':             lambda v: v,
    'layer2OctetDeltaCount':        lambda v: v,
    'bitCount':                     lambda v: v,
    'tunnelSourceIPv4Address':      lambda v: int(netaddr.IPAddress(v)),
    'tunnelDestinationIPv4Address': lambda v: int(netaddr.IPAddress(v)),
    'direction':                    lambda v: {'ingress':0, 'egress':1, 'bidirectional':2}[v],
    'ber':                          lambda v: v,
    'rxPowerMilliwatts':            lambda v: v,
    'txPowerMilliwatts':            lambda v: v,
    'rxPowerDecibelMilliwatts':     lambda v: v,
    'txPowerDecibelMilliwatts':     lambda v: v,
    'frequencyGigaHertz':           lambda v: v,
    'stlPaginationIndex':           lambda v: v,
    'stlPaginationTotal':           lambda v: v,
}

def processField(name, value, templatesCatalog=None):
    if(name.startswith('subTemplateList')):
        if(templatesCatalog is None):
            raise Exception('A TemplatesCatalog instance is required to process subTemplateList fields')

        nameParts = name.split('_')
        if(len(nameParts) != 3):
            raise Exception('subTemplateList fieldName in dataFile must have format: subTemplateList_<subTemplateId>_<semantics>')
        name_ = str(nameParts[0])
        subTemplateId = int(nameParts[1])
        chkTemplateId(subTemplateId)

        subTemplate = templatesCatalog.getTemplate(subTemplateId)
        subTemplateSemantics = parseSemantics(str(nameParts[2]))
        subTemplateList = ADT_SubTemplateList.create(subTemplateSemantics, subTemplate)
        numFields = subTemplate.getNumFields()
        
        checkString('processor_SubTemplateList.value', value)
        for vEntry in value.split(';'):
            vEntryItems = vEntry.split('|')
            if(len(vEntryItems) != numFields):
                raise Exception('SubTemplate %d requires %d fields' % (subTemplateId, numFields))
        
            dataRecord = {}
            for numField in xrange(numFields):
                nameField = subTemplate.getField(numField).getName()
                nameField_,vEntryItem = processField(nameField, vEntryItems[numField], templatesCatalog)
                dataRecord[nameField_] = vEntryItem

            subTemplateList.addDataRecord(dataRecord)
        return(name_,subTemplateList)
    else:
        parser = __FIELD_PARSERS.get(name)
        if(parser is None): raise Exception('FieldParser for %s not defined' % name)

        checker = __FIELD_CHECKERS.get(name)
        if(checker is None): raise Exception('FieldChecker for %s not defined' % name)

        translator = __FIELD_TRANSLATORS.get(name)
        if(translator is None): raise Exception('FieldChecker for %s not defined' % name)

        value = parser(value)
        checker(value)
        value = translator(value)
        return(name, value)

import math
from FieldHandlers import processField

BITS_PER_BYTE = 8
ETHER_MTU = 1500
L2TEMPLATE = 256

def __L2Traffic(sample):
    bitCount = sample['bitCount']
    byteCount = int(math.ceil(bitCount / BITS_PER_BYTE))
    packetCount = int(math.ceil(byteCount / ETHER_MTU))
    sample.update({
        'packetDeltaCount': processField('packetDeltaCount', packetCount)[1],
        'layer2OctetDeltaCount': processField('layer2OctetDeltaCount', byteCount)[1],
    })
    return(sample)

POSTCOMPUTEFUNCTIONS = {
    L2TEMPLATE: __L2Traffic
}

def postComputeFields(templateId, sample):
    func = POSTCOMPUTEFUNCTIONS.get(templateId)
    return(sample if(func is None) else func(sample))

# Reference: https://tools.ietf.org/html/rfc6313#section-4.4

from Lib.ParameterChecking import checkOptions

# The "noneOf" structured data type semantic specifies that none of
# the elements are actual properties of the Data Record.
SEMANTIC_noneOf = 0x00

# The "exactlyOneOf" structured data type semantic specifies that
# only a single element from the structured data is an actual property
# of the Data Record. This is equivalent to a logical XOR operation.
SEMANTIC_exactlyOneOf = 0x01

# The "oneOrMoreOf" structured data type semantic specifies that one
# or more elements from the list in the structured data are actual
# properties of the Data Record. This is equivalent to a logical OR
# operation.
SEMANTIC_oneOrMoreOf = 0x02

# The "allOf" structured data type semantic specifies that all of the
# list elements from the structured data are actual properties of the
# Data Record.
SEMANTIC_allOf = 0x03

# The "ordered" structured data type semantic specifies that elements
# from the list in the structured data are ordered.
SEMANTIC_ordered = 0x04

# unassigned: 0x05-0xFE

# undefined
SEMANTIC_undefined = 0xFF

SEMANTICS = [
    SEMANTIC_noneOf,
    SEMANTIC_exactlyOneOf,
    SEMANTIC_oneOrMoreOf,
    SEMANTIC_allOf,
    SEMANTIC_ordered,
    SEMANTIC_undefined
]

STRING_TO_SEMANTICS = {
    'NONEOF': SEMANTIC_noneOf,
    'EXACTLYONEOF': SEMANTIC_exactlyOneOf,
    'ONEORMOREOF': SEMANTIC_oneOrMoreOf,
    'ALLOF': SEMANTIC_allOf,
    'ORDERED': SEMANTIC_ordered,
    'UNDEFINED': SEMANTIC_undefined
}

SEMANTICS_TO_STRING = {
    SEMANTIC_noneOf: 'NONEOF',
    SEMANTIC_exactlyOneOf: 'EXACTLYONEOF',
    SEMANTIC_oneOrMoreOf: 'ONEORMOREOF',
    SEMANTIC_allOf: 'ALLOF',
    SEMANTIC_ordered: 'ORDERED',
    SEMANTIC_undefined: 'UNDEFINED'
}

def checkSemantics(semantic):
    checkOptions('semantic', semantic, SEMANTICS)

def parseSemantics(strSemantic):
    semantic = STRING_TO_SEMANTICS.get(strSemantic.upper(), None)
    if(semantic is None): raise Exception('Undefined semantic: %s' % strSemantic)
    return(semantic)

def semanticsToString(semantic):
    checkSemantics(semantic)
    strSemantic = SEMANTICS_TO_STRING.get(semantic, None)
    if(strSemantic is None): raise Exception('Undefined semantic: %s' % semantic)
    return(strSemantic)

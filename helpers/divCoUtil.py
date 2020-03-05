### Util
def cleanupParams(rawParamDict, key, formatFunc, isOptional=False):
    rawValue = rawParamDict.get(key)
    
    if isOptional and rawValue == None:
        return None
    elif rawValue:
        return formatFunc(rawValue)
    else:
        raise ValueError("missing key in param dict")
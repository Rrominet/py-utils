import json
import base64

def dictToClass(cls, dictionary) : 
    inst = cls()
    return deserialize(inst, dictionary)

def deserialize(inst, dictionary) : 
    for k in dictionary.keys() : 
        if not hasattr(inst, k) : 
            continue
        if callable(getattr(inst, k)) : 
            continue
        val = dictionary[k]
        try : 
            if isSerializable(val) : 
                setattr(inst, k, val)
            elif type(val) == list or type(val) == tuple: 
                setattr(inst, k, _deserializeList(val))
            else : 
                setattr(inst, k, deserialize(getattr(inst, k), val))
        except : pass

def _deserializeList(ls) : 
    _r = []
    for e in ls : 
        if isSerializable(e) : 
            _r.append(e)
        elif type(e) == list or type(e) == tuple : 
            _r.append(_deserializeList(e))

def jsonToClass (cls, jsonStr) : 
    dic = json.loads(jsonStr)
    return dictToClass(cls, dic)

def _serializeList(ls, filters=[]) : 
    _re = []
    for elmt in ls : 
        if isSerializable(elmt) : 
            _re.append(elmt)
        elif type(elmt) == list or type(elmt) == tuple: 
            _re.append(_serializeList(elmt, filters))
        else : 
            _re.append(classToDict(elmt, filters))

    return _re

def isSerializable(elmt) : 
    if (type(elmt) == int
            or type(elmt) == float
            or type(elmt) == bool
            or type(elmt) == tuple
            or type(elmt) == str) :
        return True 
    return False


#all attr in filters will NOT BE SERIALIZED
def classToDict(inst, filters = []) : 
    tmp = dir(inst)
    keys = []
    for k in tmp : 
        if k in filters : 
            continue
        if ("__" not in k and isSerializable(getattr(inst, k))) :
            keys.append(k)
        elif ("__" not in k and (type(getattr(inst, k)) == list or type(getattr(inst, k)) == tuple)) : 
            keys.append(k)
    dic = {}
    for k in keys : 
        val = getattr(inst, k)
        if (type(val) == list or type(val) == tuple) : 
            dic[k] = _serializeList(val)
        else : 
            dic[k] = val

    return dic

def serialize(inst, filters=[]) : 
    if type(inst) == list or type(inst) == tuple : 
        return _serializeList(inst, filters)
    else :
        return classToDict(inst, filters)

# the key is the key for the mage data in the dict
def addImageData(pdict, key, imageData) : 
    pdict[key] = base64.b64encode(imageData).decode("utf-8")


def addImage(pdict, key, filepath) : 
    f = open(filepath, "rb")
    data = f.read()
    f.close()
    addImageData(pdict, key, data)

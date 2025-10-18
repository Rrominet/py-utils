import random

def uniqId(rg=20) : 
    l = "abdcefghijklmnopqrstuvwxyz0123456789"
    id = ""
    for i in range(rg) : 
        id += random.choice(l)
    
    return id

def lineIsEmpty(l) : 
    l = l.replace("\n", "");
    l = l.replace(" ", "");
    l = l.replace("\t", "");
    l = l.replace("\r", "");
    return (" " in l)

def toList(ls) : 
    if type(ls) == list : 
        return ls
    try : 
        it = iter(ls)
    except : 
        return [ls]

    nls= []
    for i in range(len(ls)) : 
        nls.append(ls[i])

    return nls

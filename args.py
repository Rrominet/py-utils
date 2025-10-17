import sys

#_args["0"] is a positional argument.
#_args["flag"] ia a True/False argument (works also with --, the key does not contains the - or --)
#_args["option"] is an argument that take the value of the next argument (works also with --)

_args = {}
_programName = sys.argv[0]

def pgr() : 
    return _programName

def programName() : 
    return _programName

def containsDash(arg) :
    return arg[0] == "-" or arg[:1] == "--"

def dashRemoved(arg) : 
    if arg[:1] == "--" :
        return arg[2:]
    if arg[0] == "-" :
        return arg[1:]
    return arg

def parse(argv) : 
    l = len(argv)
    pos = 0
    i = 0
    while i < l :
        if i == 0 : 
            i += 1
            continue

        if (containsDash(argv[i])) : 
            if l <= i + 1 : 
                _args[dashRemoved(argv[i])] = True
            else : 
                if (containsDash(argv[i+1])) : 
                    _args[dashRemoved(argv[i])] = True
                else : 
                    _args[dashRemoved(argv[i])] = argv[i+1]
                    i += 1
        else : 
            _args[str(pos)] = argv[i]
            pos += 1
        i += 1

def flag(name) : 
    if name in _args : 
        return _args[name]
    else : 
        return False

def option(name) : 
    if name in _args : 
        return _args[name]
    else : 
        return None

def pos(idx) : 
    if str(idx) in _args : 
        return _args[str(idx)]
    else : 
        return None

def allPositional() : 
    ls = []
    for k in _args: 
        try : 
            int(k)
            ls.append(_args[k])
        except : 
            pass
    return ls

parse(sys.argv)

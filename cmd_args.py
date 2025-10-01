import json

class Command : 
    #to_exec is a function that take as args a decoded json
    def __init__(self, name, description, to_exec) : 
        self.name = name
        self.description = description
        self.to_exec = to_exec
        self.args = None

    #useful for automatic help command
    def print(self) : 
        print(self.name + " : ")
        print(self.description)

_cmds = {}

def reg(name, description, to_exec) : 
    _cmds[name] = Command(name, description, to_exec)

def exec(name, args) : 
    if name not in _cmds :
        print("Unknown command : " + name)
        return
    return _cmds[name].to_exec(args)

def printHelp() : 
    for cmd in _cmds : 
        _cmds[cmd].print()
        print("")


#your json should have the following structure :
#{
#    "cmd" : "cmd_name",
#    "args" : [arg1, arg2, arg3]
#}
def execFromArgs(args) : 
    if len(args) == 1 :
        print("No args given, abort.")
        return

    if "--help" in args : 
        printHelp()
        return
    else : 
        data = json.loads(args[1])
        if "args" in data :
            exec(data["cmd"], data["args"])
        else : 
            exec(data["cmd"], [])

def outsuccess() : 
    data = {"success" : True}
    print(json.dumps(data))

def outdata(data) : 
    data = {"success" : True, "data" : data}
    print(json.dumps(data))

def outerror(data) :
    data = {"success" : False, "data" : str(data)}
    print(json.dumps(data))

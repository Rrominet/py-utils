import json
import sys
import threading
import queue
from typing import Callable, Dict, Any
from dataclasses import dataclass


#this framework is useed when stuff is sended to the stdin
#the process stay alive after receive() is called and wait for any input in stdin
#It's not a call by argument when the program start, for this the the lib cmd_args.py

_reqId = 0
_registersLock = threading.Lock()
_registers: Dict[str, Callable] = {}

@dataclass
class Process:
    callbacks: list
    write: Callable

    def addOnOutput(self, callback):
        self.callbacks.append(callback)

    def onOutput(self):
        return self.callbacks

def reqId():
    global _reqId
    _reqId += 1
    return _reqId - 1

def addToResponse(process: Process, idArg: int, callback: Callable):
    idx = len(process.onOutput())

    def wrapper(line: str):
        try:
            j = json.loads(line)
            if j["id"] == idArg:
                callback(j)
                # Disable this callback after firing
                process.onOutput()[idx] = lambda x: None
        except Exception as e:
            print(f"Cannot parse line for ipc response: {line}", file=sys.stderr)
            print(str(e), file=sys.stderr)

    process.addOnOutput(wrapper)

def send(process: Process, data: dict, callback: Callable = None):
    toSend = data.copy()
    toSend["id"] = reqId()
    process.write(json.dumps(toSend))
    if callback:
        addToResponse(process, toSend["id"], callback)

def call(process: Process, function: str, args: dict, callback: Callable = None):
    toSend = {
        "function": function,
        "args": args
    }
    send(process, toSend, callback)

#reg for register fucntion
#the json returned by the function is the response from the function that the process caller will receive.
#the json returned json could follow this standard : 
#{
#    "success" : true/false,
#    "message" : "some message to add context or infos if the call was successfull",
#    "data" : {...},
#    "error" : "some error message if the call failed"
#}
def reg(function: str, todo: Callable):
    with _registersLock:
        _registers[function] = todo

def onStdinLine():
    def handler(line: str):
        try:
            received = json.loads(line)
        except Exception as e:
            return

        try:
            funcName = received["function"]
        except KeyError:
            return

        with _registersLock:
            if funcName in _registers:
                args = {}
                if "args" in received:
                    args = received["args"]
                res = _registers[funcName](args)
                try : 
                    res["id"] = received["id"]
                except : pass
                print(json.dumps(res), flush=True)
            else:
                res = {
                    "message": f"Function not found: {funcName}",
                    "success": False
                }
                print(json.dumps(res), flush=True)
    return handler

def receive():
    while True:
        line = sys.stdin.readline()
        if line:
            onStdinLine()(line.strip())
        else : 
            break

def initAsReceiver():
    thread = threading.Thread(target=receive, daemon=True)
    thread.start()

def error(toReturn: dict, message: str):
    toReturn["success"] = False
    toReturn["error"] = message

def errorIfNotExists(toCheck: dict, toReturn: dict, key: str, ctxMessage: str = "") -> bool:
    if key not in toCheck:
        toReturn["success"] = False
        toReturn["error"] = f"Missing key: {key}{' (' + ctxMessage + ')' if ctxMessage else ''}"
        return True
    return False

def success(toReturn: dict):
    toReturn["success"] = True
    toReturn["error"] = ""

# how to use it as a receiver :
# the caller is not doned yet because the Process class is not implemented fully. 
#reg("hello", lambda x: {"message": "Hello " + x["name"]})
#receive()

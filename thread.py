from threading import Thread

class TmpThread (Thread) : 
    def __init__(self, func) : 
        Thread.__init__(self)
        self.func = func

    def run (self) : 
        self.func()

def start(func) : 
    """ launch the func on a different thread """
    tmp = TmpThread(func) 
    tmp.deamon = True
    tmp.start()

def startOnObj(method, owner) : 
    """ Lauch the method with its owner on a different thread """
    def func () : 
        method(owner)

    tmp = TmpThread(func)
    tmp.deamon = True
    tmp.start()

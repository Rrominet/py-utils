
#Its a thread safe event that will always trigger a function that will be executed on the main thread (using run or the one returned by the run_async function) regardless of where the event is emitted.
import threading

mainQ = []
cv = threading.Condition()
class Event : 
    def __init__(self):
        self.id = "" #could be use to filter them if needed.
        self.listeners = []
        self.user_data = None

    def addListener(self, listener):
        self.listeners.append(listener)
        return len(self.listeners) - 1

    def removeListener(self, index):
        if (index < 0 or index >= len(self.listeners)):
            print ("removeListener : Index out of range " + str(index) + "/" + str(len(self.listeners)))
            return
        self.listeners[index] = None

    def clear(self):
        self.listeners = []

    def emit(self) : 
        with cv :
            for l in self.listeners :
                if l : 
                    mainQ.append(l)
            cv.notifyAll()

def run() : 
    global mainQ
    while(True) : 
        with cv : 
            cv.wait_for(lambda : len(mainQ) > 0)
            for l in mainQ :
                l()
            mainQ = []

def run_async() : 
    t = threading.Thread(target=run)
    t.start()
    return t


import time
ev_test = Event()
def periodic_test() : 
    while(True) :
        time.sleep(1)
        ev_test.emit()

def test() : 
    ev_test.addListener(lambda : print ("Test 1"))
    threading.Thread(target=periodic_test).start()
    run()

#for this to work, specially the log.p func, you need to create a environment variable LOG=1
#for linux for example : export LOG=1 in you terminal session

try : 
    from lpqflv import fileTools as ft
except :
    from ml import fileTools as ft
import os
import timeit

TEMP_DIR = "/media/romain/Donnees/TEMP/BLENDER_TEMP/LPQFLV_TMP"
LOG = TEMP_DIR + "/log.txt"

dolog = os.getenv("LOG", '0')
if dolog == '1' : 
    dolog = True
else : 
    dolog = False

def replace(content, debug) : 
	if debug : 
		ft.writeInFile(LOG, content)

def append(content, debug) : 
	if debug : 
		ft.appendToFile(LOG, content + "\n") 

def write(content, debug=True) : 
	append(content, debug)

def p(content) : 
    if dolog :
        print(content)

def log(content) : 
    p(content)

def measurePerfs() : 
    setup = "dolog = True"
    testone = """
print ("this is a test string.")
    """

    testtwo = """
if dolog : 
    print("this is a test string.")
"""

    testonetime = timeit.timeit(stmt=testone, setup=setup, number=1000)
    testtwotime = timeit.timeit(stmt=testtwo, setup=setup, number=1000)
    print ("Test (print) without IF :") 
    print(testonetime)

    print ("Test (print) with IF :")
    print(testtwotime)

    ratio = testonetime / testtwotime
    print ("Witout IF (print), the execution take " + str(ratio) + "x the IF execution.")

    test3 = """
a = True
    """

    test4 = """
if dolog : 
    a = True
"""

    test3time = timeit.timeit(stmt=test3, setup=setup, number=1000)
    test4time = timeit.timeit(stmt=test4, setup=setup, number=1000)
    print ("Test without IF :") 
    print(test3time)

    print ("Test with IF :")
    print(test4time)

    ratio = test3time / test4time
    print ("Witout IF, the execution take " + str(ratio) + "x the IF execution.")


colors = {
        "black" : "\u001b[30m",
        "red" : "\u001b[31m",
        "green" : "\u001b[32m",
        "yellow" : "\u001b[33m",
        "blue" : "\u001b[34m",
        "purple" : "\u001b[35m",
        "cyan" : "\u001b[36m",
        "white" : "\u001b[37m"
        }

# this will always print regardless of the environment variable
def print(content, color="white") : 
    __builtins__["print"](colors[color] + content + "\u001b[0m")

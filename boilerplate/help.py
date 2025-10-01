import os

def nvim() : 
    return os.path.dirname(__file__) + os.sep + "doc" + os.sep + "nvim.txt"

def compile() : 
    return os.path.dirname(__file__) + os.sep + "doc" + os.sep + "compile.txt"

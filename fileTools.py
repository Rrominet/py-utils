# -*-coding:utf-8 -*
import os
import heapq

def writeInFile(pPath, content, mkDirs=True):
    path = pPath.replace("\\", "/")
    if mkDirs:
        tmp = path.split("/")
        i = 0
        dirPath = ""
        for s in tmp:
            if i != len(tmp) - 1:
                dirPath += "/" + s
            i += 1

        try:
            os.makedirs(dirPath)

        except:
            pass

    file = open(path, "w")
    res = file.write(content)
    file.close()

    return res


def write(data, path, mkDirs=True):
    writeInFile(path, data, mkDirs)

def createTree(path):
    tmp = path.split(os.sep)
    path = ""
    import platform
    if platform.system == "Windows":
        path = tmp[0]
        tmp = tmp[1:]
    for w in tmp:
        path += w + os.sep
        if not os.path.isdir(path):
            os.mkdir(path)


def appendToFile(path, content):
    if not os.path.exists(path):
        try:
            os.makedirs(folder(parentDir(path)))
        except:
            pass
        file = open(path, "w")
        res = file.write(content)
        file.close()
        return res
    else:
        file = open(path, "a")
        res = file.write(content)

        file.close()
        return res


append = appendToFile

def readFileContent(path):
    if os.path.isdir(path):
        return ""
    if not os.path.exists(path):
        return ""

    file = open(path, "r")
    r = ""
    try:
        r = file.read()
    except:
        pass

    file.close()
    return r


def readFile(path):
    """Allias of 'readFileContent'"""
    return readFileContent(path)


def read(path):
    """Allias of 'readFileContent'"""
    return readFileContent(path)


def replaceInFile(path, search, replace):
    txt = read(path)
    txt = txt.replace(search, replace)
    write(txt, path)


def readFileLines(path):
    file = open(path, "r")
    lines = file.readlines()

    file.close()
    return lines


def getBoolFromStr(string):
    if string == "0":
        return False
    else:
        return True


def getStrFromBool(pBool):
    if pBool == True:
        return "1"

    else:
        return "0"


def getCleanPath(path):
    path = path.replace("\\", "/")

    if os.path.isdir(path):
        if path[len(path) - 1 == "/"]:
            pass
        else:
            path += "/"

    return path


def getGlobalFromLocal(path):
    import bpy

    if ("//" in path):
        filepath = bpy.data.filepath
        filepath = getCleanPath(filepath)

        currentDirLst = bpy.data.filepath.split(
            "/")[:len(bpy.data.filepath.split("/"))-1]
        currentDir = getCleanPath("/".join(currentDirLst))

        path = path.replace("//", "")

        path = currentDir + "/" + path
        return path

    else:
        return path


def fileSize(path):
    if not os.path.exists(path):
        return 0
    return os.stat(path).st_size


def ext(file):
    if "." not in file:
        return ""
    return file.split(".")[-1]


def noExt(file):
    if "." not in file:
        return file
    tmp = file.split(".")[:-1]
    return ".".join(tmp)

def baseName(file) : 
    return noExt(file.split(os.sep)[-1])

class File:
    def __init__(self, path):
        self.path = path

    def size(self):
        return fileSize(self.path)

    def idem(self, pFile):
        if self.size() == pFile.size():
            return True
        else:
            return False


def hierarchie(root, includeDirs=True, filterDirs=[]):
    if root[-1] == "/":
        root = root[:-1]
    files = os.listdir(root)

    i = 0
    max = len(files)
    while i < max:
        files[i] = root + "/" + files[i]
        if os.path.isdir(files[i]):
            if os.path.basename(files[i]) not in filterDirs:
                files += hierarchie(files[i], includeDirs, filterDirs)

        i += 1

    if not includeDirs:
        ok = []
        for f in files:
            if os.path.isdir(f):
                continue
            else:
                ok.append(f)
        return ok

    return files


def cleanPath(path, checkIfExist=True, removeLastSlash=True):
    if not os.path.exists(path) and checkIfExist:
        return False

    if len(path) == 0:
        return False

    path = path.replace("\\", "/")
    path = path.replace("//", "/")

    if path[-1] == "/" and removeLastSlash:
        path = path[:-1]

    return path


def folder(path):
    l = cleanPath(path, False, False).split("/")
    l = l[:-1]

    return "/".join(l)


def filename(path):
    return cleanPath(path, False, False).split("/")[-1]

def parentDir(path):
    return folder(path)
def parent(path) : return folder(path)

def findFile(root, filename):
    files = os.listdir(root)
    file = None
    for f in files:
        if f == filename:
            return root + os.sep + f
        elif os.path.isdir(root + os.sep + f):
            file = findFile(root + os.sep + f, filename)
            if file:
                return file
    return file

#return the naes, not the full path
def findInDir(dir, extension) : 
    _r = []
    for f in os.listdir(dir) : 
        if f[-len(extension)-1:] == "." + extension : 
            _r.append(f)

    return _r


def removeOldestFiles(directory, max_files=100):
    # Get all files in the directory
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Check if the number of files exceeds the limit
    if len(files) > max_files:
        # Determine how many files to remove
        num_files_to_remove = len(files) - max_files

        # Create a min heap based on file modification times
        # Heap item: (modification_time, file_path)
        heap = [(os.path.getmtime(file), file) for file in files]
        heapq.heapify(heap)

        # Remove the oldest files
        for _ in range(num_files_to_remove):
            _, file_to_remove = heapq.heappop(heap)
            os.remove(file_to_remove)

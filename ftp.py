from ftplib import FTP
import os

if __name__ == "lpqflv.ftp" : 
    from lpqflv import fileTools as ft
else : 
    import fileTools as ft


def login(server, username, pw, debug=1, encoding='utf-8') : 
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftp.connect(server, 21) 
    ftp.login(username, pw)
    ftp.encoding = encoding

    return ftp


def filter(files, root='', folder=True, extensions=[], maxSize=10000000000000000000000) : 
    _r = []
    for f in files : 
        if folder and os.path.isdir(f) : 
            continue
        
        if ext(f) in extensions : 
            continue

        if os.path.getsize(f) > maxSize : 
            continue

        else : 
            _r.append(f.replace(root, ''))

    return _r

def makePath(path, ftp) : 
    dirs = path.split("/")
    
    fullDirs = []
    for i in range(0, len(dirs)) :
        path = ""
        for j in range(0, i+1) : 
            path += dirs[j] + "/"
        fullDirs.append(path[:-1])

    for fd in fullDirs : 
        try : 
            ftp.mkd(fd)
        except : 
            pass 

def sameSize(local, server, ftp) : 
    try : 
        ssize = ftp.size(server)
        lsize = os.path.getsize(local)

        if ssize == lsize : 
            return True
        else : 
            return False
    except : 
        return False

def cleanPath(server) : 
    return server

def upload(local, server, ftp) : 
    if not os.path.exists : 
        return
    elif os.path.isdir(local) : 
        return 

    if not sameSize(local, server, ftp) : 
        fp = open(local, 'rb')
        ftp.storbinary('STOR %s' % cleanPath(server), fp)
        fp.close()

def download(server, local, ftp) :
    if not sameSize(local, server, ftp) : 
        fl = open(local, 'wb')
        ftp.retrbinary('RETR %s' % cleanPath(server), fl.write)

def listDir(server, ftp) : 
    files = []
    try : 
        filesGenerator = ftp.mlsd(server) 
        for f in filesGenerator : 
            files.append(f[0])
    except : 
        pass

    return files

def allFiles(server, ftp) : 
    lists = listDir(server, ftp)
    files = []
    for f in lists : 
        if f == "." or f==".." : 
            continue
        if not isDir(server + "/" + f, ftp) : 
            files.append(server + "/" + f)
        else : 
            files.extend(allFiles(server + "/" + f, ftp))

    return files

def isDir(server, ftp) : 
    resp = ftp.sendcmd('MLST ' + server)
    if "type=dir" in resp : 
        return True
    else : 
        return False

def cloneDirsFromServer(server, local, ftp, filterExt = [], filterNames = []) : 
    files = listDir(server, ftp)
    for f in files : 
        path = server + "/" + f
        localPath = local + "/" + f

        if f == "." or f == ".." : 
            continue

        if f in filterNames : 
            print("don't download this file/dir because it's filtered.")
            continue

        if isDir(path, ftp) : 
            if os.path.exists(localPath) and not os.path.isdir (localPath) and ft.ext(localPath) == "" : 
                os.remove(localPath)
            try : os.mkdir(localPath)
            except : pass
            cloneDirsFromServer(path, localPath, ftp, filterExt)

        elif ft.ext(path) not in filterExt : 
            try : download(path, localPath, ftp)
            except : print ("can't download : " + path)

        if os.path.exists(localPath) and not os.path.isdir (localPath) and os.path.getsize(localPath) == 0 : 
            os.remove(localPath)

def cloneDirsFromLocal(local, server, ftp, filterExt = []) : 
    localFiles = ft.hierarchie(local, False)
    for i in range(len(localFiles)) :
        localFiles[i] = localFiles[i].replace(local, "")

    for f in localFiles : 
        localPath = local + f
        serverPath = server + "/" + f
        if ft.ext(f) in filterExt : 
            continue
        try : 
            upload(localPath, serverPath, ftp)
        except : 
            makePath(os.path.split(serverPath)[0], ftp)
            upload(localPath, serverPath, ftp)


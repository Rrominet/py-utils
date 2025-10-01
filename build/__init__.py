from ml import fileTools as ft
from ml import log
import os
import platform
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
import json

debug = 1
release = 2

OK = 0
ERROR = 1

class Project : 
    def __init__(self, name) : 
        self.name = name
        self.build_dir = os.getcwd()
        self.obj_dir = self.build_dir + os.sep + ".obj"
        self.cache_dir = self.build_dir + os.sep + ".cache"
        self.modules_dir = self.build_dir + os.sep + "gcm.cache"
        self.compile_commands = []
        self.export_compile_commands = True
        self.builder = "g++"
        self.includes = []
        self.lib_dirs = []
        self.rpath_dirs = []
        self.libs = [] # names
        self.libsPaths = []
        self.srcs = []
        self.modules = []
        self.definitions = ["pthread"] # #define
        self.flags = [] # -O3 or -g
        self.futures = []
        self.state = OK
        self.static = False
        self.useThreads = True
        self.shared = False #True if you want to build as a shared lib and not as a programm
        self.useModules= False
        self.srcs_exclude = []
        self.release = False

    #type is debug or release
    def setType(self, type) : 
        if type == debug and self.builder == "g++":
            self.flags.append("Og")
            self.flags.append("g")
        elif type == debug and self.builder == "em++" :
            self.flags.append("O0")
            self.flags.append("gsource-map")
            self.flags.append("-fexceptions")
            self.flags.append("-fsanitize=undefined")
            self.flags.append("-ASSERTIONS=1 ")

        if type == debug : 
            self.definitions.append("mydebug")
            self.definitions.append("mldebug")
            #self.flags.append("-fsanitize=address")

        if type == release and self.builder == "g++" :
            self.flags.append("O3")
        elif type == release and self.builder == "em++" :
            self.flags.append("Os")

    def setFromArgs(self, args) : 
        if "release" in args :
            self.setType(release)
            self.release = True
        else : 
            self.setType(debug)

    def obj(self, srcfilepath) : 
        return self.obj_dir + os.sep + os.path.basename(ft.noExt(srcfilepath)) + ".o"

    def module(self, srcfilepath) : 
        return self.modules_dir + os.sep + os.path.basename(ft.noExt(srcfilepath)) + ".o"

    def cache(self, srcfilepath) : 
        return self.cache_dir + os.sep + os.path.basename(ft.noExt(srcfilepath) + ".cache")

    def listAsArgs(self, ls, prefix="") :
        l = []
        for i in ls : 
            if not i.startswith(prefix) :
                l.append(prefix + i)
            else : 
                l.append(i)
        return l

    def flagsAsArgs(self, flags) : 
        l = []
        for f in flags :
            if f[0] == "-" : 
                l.append(f)
            else : 
                l.append("-" + f)

        return l

    def compileCommand(self, srcfilepath) : 
        cmd = [self.builder]
        if ft.ext(srcfilepath) == "c" : 
            cmd.append("-x")
            cmd.append("c")

        if self.shared : 
            cmd += ["-c", "-fPIC", srcfilepath,
                    "-o", self.obj(srcfilepath)]
        else : 
            cmd += ["-c", srcfilepath,
                    "-o", self.obj(srcfilepath)]

        cmd.extend(self.listAsArgs(self.includes, "-I"))
        cmd.extend(self.listAsArgs(self.definitions, "-D"))
        cmd.extend(self.flagsAsArgs(self.flags))
        if self.export_compile_commands : 
            o_cmd = {}
            o_cmd["directory"] = os.getcwd()
            o_cmd["command"] = " ".join(cmd)
            o_cmd["file"] = srcfilepath
            self.compile_commands.append(o_cmd)
        return cmd

    def compile(self) : 
        log.print("Starting compilation...")
        if not os.path.exists(self.obj_dir) :
            os.mkdir(self.obj_dir)

        fns = []
        for src in self.srcs : 
            log.print("Adding " + src, "yellow")
            def comp(src=src) : 
                if src.split(os.sep)[-1] in self.srcs_exclude :
                    log.print("Skipping " + src.split(os.sep)[-1] + " because it is in the exclude list.", "yellow")
                    return
                # execute this first to add the command to compile_commands.json even if not executed.
                log.print("Compiling " + src, "yellow")
                cmd = self.compileCommand(src)
                if not self.needRebuild(src) :
                    log.print("No changes in " + src, "yellow")
                    return
                self.logCmd(cmd)
                ret = subprocess.call(cmd)
                if ret != 0 :
                    log.print("Compilation error with " + os.path.basename(src), "red")
                    self.state = ERROR
                    os.remove(self.cache(src))
                    self.killCompile()
                    for f in self.futures :
                        f.cancel()
                    raise Exception("Compilation error")
                else : 
                    log.print(os.path.basename(src) + " compiled.\n", "green")
            fns.append(comp)
        self.exec(fns)

        if self.export_compile_commands :
            f = open(self.build_dir + os.sep + ".." + os.sep + "compile_commands.json", "w")
            f.write(json.dumps(self.compile_commands))
            f.close()

        log.print("Compilation doned.\n", "yellow")

    def exec(self, funcs) : 
        if self.useThreads :
            self.futures = []
            mx = os.cpu_count()
            pool = ThreadPoolExecutor(max_workers=mx)

            for fn in funcs : 
                self.futures.append(pool.submit(fn))

            for f in self.futures : 
                f.result()
        else : 
            for fn in funcs :
                fn()

    def killCompile(self) : 
        if platform.system() == "Windows" : 
            os.system("taskkill /IM " + self.builder + " /F")
            os.system("taskkill /IM cc1plus.exe /F")
        else : 
            os.system("killall -SIGKILL " + self.builder)
            os.system("killall -SIGKILL cc1plus")

    def logCmd(self, cmd) : 
        s = "\u001b[36m"
        for i in cmd : 
            s += i + " "
        s += "\u001b[36m"
        log.print(s, "cyan")

    def libsAsArgs(self) :
        l = []
        for i in self.libs : 
            if ft.ext(i) == "a" or ft.ext(i) == "lib" :
                l.append(i)
            else :
                if not i.startswith("-l") :
                    l.append("-l" + i)
                else : 
                    l.append(i)
        return l

    def link(self) : 
        if self.state == ERROR :
            log.print("Cannot link " + self.name + " there was an error in build.", "red")
            return
        log.print("Starting linking process...")
        self.createSharedLibsSymlinks()
        cmd = [self.builder]
        if self.shared : 
            cmd.extend(["-shared"])
        cmd.extend(self.flagsAsArgs(self.flags))
        if self.static :
            cmd.extend(["-static", "-static-libgcc", "-static-libstdc++"])

        for s in self.srcs : 
            if s.split(os.sep)[-1] in self.srcs_exclude :
                continue
            cmd.append(self.obj(s))

        cmd.append("-o")
        if (self.builder == "em++" or self.builder == "emcc") :
            cmd.append(self.build_dir + os.sep + self.name + ".js")
        else : 
            cmd.append(self.build_dir + os.sep + self.getFileName())

        cmd.extend(self.libsPaths)
        cmd.extend(self.listAsArgs(self.lib_dirs, "-L"))
        cmd.extend(self.libsAsArgs())

        if self.rpath_dirs != [] :
            cmd.append(self.rpathAsArgs())

        self.logCmd(cmd)
        ret = subprocess.call(cmd)

        if ret != 0 :
            log.print("Linking error.", "red")
            raise Exception("Linking error")

        log.print("Linking doned.\n", "yellow")

    def getFileName(self) : 
        if self.shared : 
            return "lib" + self.name + ".so"
        else : 
            return self.name

    def clean(self) : 
        log.print("Cleaning " + self.name + " project ...")
        try :
            shutil.rmtree(self.obj_dir)
        except : pass
        try :
            shutil.rmtree(self.cache_dir)
        except : pass
        os.mkdir(self.cache_dir)
        try : 
            os.remove(self.build_dir + os.sep + self.getFileName())
        except : pass

        try : 
            shutil.rmtree(self.build_dir + os.sep + "gcm.cache")
        except : pass

        try : 
            shutil.rmtree(self.build_dir + os.sep + ".cache")
        except : pass

        log.print("Cleaning done.\n", "green")

    def install(self) : 
        pass

    def makeExecutable(self, filepath) :
        if self.builder == "em++" : 
            return
        cmd = ["chmod", "+x", filepath]
        self.logCmd(cmd)
        subprocess.call(cmd)

    def cleanIfNeeded(self) : 
        try : 
            data = open(self.cache_dir + os.sep + "settings", "r").read()
            if data != self.currentSettings() :
                self.clean()
        except : 
            self.clean()

    def currentSettings(self) :
        s = self.name + "\n"
        s += ",".join(self.flags) + "\n"
        s += ",".join(self.definitions) + "\n"
        s += ",".join(self.includes) + "\n"
        return s

    def writeSettings(self) : 
        if not os.path.exists(self.cache_dir) : 
            os.mkdir(self.cache_dir)
        f = open(self.cache_dir + os.sep + "settings", "w")
        f.write(self.currentSettings())

    def build(self) : 
        if self.state == ERROR :
            log.print("Cannot build " + self.name + " there was an error in configuration.", "red")
            return

        self.cleanIfNeeded()
        self.writeSettings()
        try : 
            log.print("Start building " + self.name)
            self.compile()
            self.link()
            self.makeExecutable(self.build_dir + os.sep + self.name)
            log.print("Done.\nExecutable is " + self.build_dir + os.sep + self.getFileName() + "\n", "green")
        except Exception as e : print(e)

    #if the src is a file, it will be added to srcs
    #if the src is a directory, all of its contents will be added
    #if reccursive is true, the contents of subdirectories will be added
    def addToSrcs(self, src, reccursive=False) : 
        if type(src) == list or type(src) == tuple : 
            for s in src :
                self.addToSrcs(s, reccursive)
            return 

        if not os.path.exists(src) : 
            src = os.getcwd() + os.sep + src
            if not os.path.exists(src) : 
                raise Exception("Source not found : " + src)

        if os.path.isdir(src) : 
            if reccursive : 
                for f in os.listdir(src) : 
                    self.addToSrcs(src + os.sep + f)
            else : 
                for f in os.listdir(src) : 
                    if ft.ext(f) == "c" or ft.ext(f) == "cpp" or ft.ext(f) == "cc" :
                        self.srcs.append(src + os.sep + f)
                    elif ft.ext(f) == "ixx" :
                        self.modules.append(src + os.sep + f)
        else : 
            if ft.ext(src) == "c" or ft.ext(src) == "cpp" or ft.ext(f) == "cc" :
                self.srcs.append(src)
            elif ft.ext(src) == "ixx" :
                self.modules.append(src)

    def addToLibs(self, lib) : 
        if type(lib) == list or type(lib) == tuple :
            for s in lib :
                self.addToLibs(s)
            return

        if os.path.exists(lib) : 
            self.libsPaths.append(lib)
            return

        if ft.ext(lib) == "a" or ft.ext(lib) == "lib" :
            if not os.path.exists(lib) :
                log.print("Library not found : " + lib, "red")
                self.state = ERROR
            self.libs.append(lib)
        else : 
            if lib[0:3] == "lib" :
                self.libs.append(lib[3:].replace(".so", ""))
            else : 
                self.libs.append(lib.replace(".so", ""))
 
    def needRebuild(self, src) : 
        r = False
        if not os.path.exists(self.obj(src)) : 
            r = True
        if not os.path.exists(self.cache(src)) :
            r = True
        current = os.path.getsize(src)
        cmd = [self.builder, "-MM", src]
        cmd.extend(self.listAsArgs(self.includes, "-I"))
        ret = subprocess.run(cmd, capture_output=True)
        headers = ret.stdout.decode("utf-8").split("\\\n")
        headers = headers[1:]
        headers = headers[:-1]
        for h in headers : 
            while h[-1] == " " : 
                h = h[:-1]

            while h[0] == " " : 
                h = h[1:]

            if " " in h : 
                tmp = h.split(" ")
                h = tmp[0]
                for i in range(1, len(tmp)) :
                    headers.append(tmp[i])

            current += os.path.getsize(h)

        if os.path.exists(self.cache(src)) :
            prev = int(open(self.cache(src), "r").read())
        else :  
            prev = 0
        if prev != current : 
            r = True
        open(self.cache(src), "w").write(str(current))
        return r

    def addToLibDirs(self, dir) : 
        if type(dir) == list or type(dir) == tuple :
            for s in dir :
                self.addToLibDirs(s)
            return

        if not os.path.exists(dir) :
            self.state = ERROR
            log.print("Directory of shared libraries not found : " + dir, "red")
            return

        if dir[0:2] == "./" : 
            self.rpath_dirs.append("$ORIGIN" + dir[1:])
            self.lib_dirs.append(os.getcwd() + dir[1:])
        else : 
            self.rpath_dirs.append(dir)
            self.lib_dirs.append(dir)

    def createSharedLibsSymlinks(self) : 
        log.print("Create libs symlinks if needed.", "yellow")
        for d in self.lib_dirs :
            self.createSharedLibsSymlinksInDir(d)
        log.print("Symlinks created.", "green")

    def createSharedLibsSymlinksInDir(self, dir) : 
        for f in os.listdir(dir) : 
            tmp = f.split(".so")
            if len(tmp) == 2 : 
                if not os.path.exists(dir + os.sep + tmp[0] + ".so") :
                    try :
                        os.symlink("./" + f, dir + os.sep + tmp[0] + ".so")
                    except : pass

    def rpathAsArgs(self) : 
        rpath = ""
        for p in self.rpath_dirs :
            rpath += p + ":"
        rpath = rpath[:-1]
        rpath = "-Wl,-rpath," + rpath
        return rpath

    #using pkg-config
    def addInstalledLibrary(self, libname) : 
        includes = []
        flags = []
        libs = []


        cmd = ["pkg-config", "--cflags", libname]
        ret = subprocess.run(cmd, capture_output=True)
        _flags = ret.stdout.decode("utf-8")

        for f in _flags.split(" ") : 
            if f.startswith("-I") :
                includes.append(f)
            elif f.startswith("-") : 
                flags.append(f)

        cmd = ["pkg-config", "--libs", libname]
        ret = subprocess.run(cmd, capture_output=True)
        _libs = ret.stdout.decode("utf-8")

        for l in _libs.split(" ") :
            if l.startswith("-l") :
                libs.append(l)

        self.includes += includes
        self.flags += flags
        self.libs += libs

    def setForModules(self) : 
        self.flags += ["-std=c++20", "-fmodules-ts"]
        self.useModules = True

    def makeSingleThreaded(self) : 
        self.useThreads = False

    def addEmiscriptenFlags(self) :
        self.flags += ["-sFETCH", "-s", "LLD_REPORT_UNDEFINED", "-lembind", "-std=c++17"]

    #filepath is relative the project build dir
    def write(self, filepath, content) :
        content = "//This is a generated file, don't change it manually, it will be override when rebuild.\n\n" + content
        if not os.path.exists(self.build_dir + os.sep + filepath) :
            ft.write(content, self.build_dir + os.sep + filepath)
            return True

        _tmp = ft.read(self.build_dir + os.sep + filepath)
        if _tmp == content : 
            return False
        else : 
            ft.write(content, self.build_dir + os.sep + filepath)
            return True

def create(name, argv=[], builder="g++") : 
    _r = Project(name)
    _r.builder = builder
    if len(argv) > 0 :
        _r.setFromArgs(argv)
    return _r



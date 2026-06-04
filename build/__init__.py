from ml import fileTools as ft
from ml import log
import os
import platform
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
import json
import re
import hashlib

debug = 1
release = 2

OK = 0
ERROR = 1

KEEP_SAME = 1
INCR_MINOR = 2
INCR_MED = 3
INCR_MAJOR = 4

BUILD = 1
SET_VERSION = 2

PROGRAMM = 1
SHARED_LIB = 2
STATIC_LIB = 3

class PackageSettings : 
    def __init__(self) : 
        self.rootDir = ""
        self.uploadDir = ""
        self.database = ""
        self._toCopy = []

    #the dest is relative to the rootDir (the distrib dir)
    def addToCopy(self, path, dest) : 
        self._toCopy.append((path, dest))

class Project : 
    def __init__(self, name) : 
        self.name = name
        self.versionAction = None
        self.version = "0.0.0"
        self.build_dir = os.getcwd()
        self.obj_dir = self.build_dir + os.sep + ".obj"
        self.cache_dir = self.build_dir + os.sep + ".cache"
        self.modules_dir = self.build_dir + os.sep + "gcm.cache"
        self.compile_commands = []
        self.export_compile_commands = True
        self.builder = "g++"
        self.includes = []
        self.lib_dirs = []
        self.rpath_dirs = ["$ORIGIN", "$ORIGIN/../lib", "$ORIGIN/lib"]
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
        self.shared = False #True if you want to build as a shared lib and not as a programm, depreciated, use outputType in new projects.
        self.outputType = PROGRAMM
        self.useModules= False
        self.srcs_exclude = []
        self.dependencies = {}
        self.release = False
        self.packageSettings = PackageSettings()
        self.mode = BUILD

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
            self.flags.append("-gsplit-dwarf")
        else : 
            self.definitions.append("NDEBUG")

        if type == release and self.builder == "g++" :
            self.flags.append("O3")
        elif type == release and self.builder == "em++" :
            self.flags.append("Os")

    def setFromArgs(self, args) : 
        if "set-version" in args : 
            self.mode = SET_VERSION
        if "release" in args :
            self.setType(release)
            self.release = True
        else : 
            self.setType(debug)

        if "keep-same" in args : 
            self.versionAction = KEEP_SAME
        elif "incr-minor" in args : 
            self.versionAction = INCR_MINOR
        elif "incr-med" in args : 
            self.versionAction = INCR_MED
        elif "incr-major" in args : 
            self.versionAction = INCR_MAJOR

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

        if self.shared or self.outputType == SHARED_LIB : 
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
        if self.outputType == STATIC_LIB :
            cmd = ["ar"]
            cmd.append("rcs")
            cmd.append("lib" + self.name + ".a")
            for s in self.srcs : 
                if s.split(os.sep)[-1] in self.srcs_exclude :
                    continue
                cmd.append(self.obj(s))
            self.logCmd(cmd)
            ret = subprocess.call(cmd)
            if ret != 0 :
                log.print("Linking error.", "red")
                raise Exception("Linking error")

            log.print("Linking doned.\n", "yellow")
            return

        cmd = [self.builder]
        cmd.append("-fuse-ld=mold")
        if self.shared or self.outputType == SHARED_LIB : 
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
        if self.outputType == SHARED_LIB : 
            return "lib" + self.name + ".so"
        elif self.outputType == STATIC_LIB :
            return "lib" + self.name + ".a"
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

    def lastVersion(self) : 
        if os.path.exists(self.build_dir + os.sep + "version") :
            self.version = ft.read(self.build_dir + os.sep + "version")
        return self.version

    def setVersion(self, version) : 
        self.version = version
        ft.write(self.version, self.build_dir + os.sep + "version")

    def askVersion(self) : 
        log.print ("Last version is " + self.lastVersion(), "yellow")
        v = input("New version : ")
        if (v == "") :
            log.print("Keeping the last version : " + self.lastVersion(), "yellow")
            v = self.lastVersion()
        self.setVersion(v)

    def updateVersion(self): 
        last = self.lastVersion()
        if self.versionAction == KEEP_SAME :
            log.print("Keeping the last version : " + last, "yellow")
            self.setVersion(last)
            return
        log.print ("Last version : " + last, "yellow")
        last = last.split(".")
        if self.versionAction == INCR_MINOR :
            log.print ("Incrementing minor...")
            minor = int(last[-1]) + 1
            last[-1] = str(minor)
        elif self.versionAction == INCR_MED :
            log.print ("Incrementing medium...")
            try : 
                med = int(last[-2]) + 1
                last[-2] = str(med)
            except : 
                last[-1] = str(int(last[-1]) + 1)
        elif self.versionAction == INCR_MAJOR :
            log.print ("Incrementing major...")
            last[0] = str(int(last[0]) + 1)

        log.print("New version : " + ".".join(last), "yellow")
        self.setVersion(".".join(last))

    def checkIncludesPaths(self) :
        for inc in self.includes :
            tocheck = inc.replace("-I", "")
            log.print("Checking include path " + tocheck, "yellow")
            if not os.path.exists(tocheck) :
                log.print("The include path " + inc + " does not exist.", "red")
                raise Exception("The include path " + inc + " does not exist.")
            if not os.path.isdir(tocheck) :
                log.print("The include path " + inc + " is not a directory. Ignoring...", "orange")

        log.print("Includes paths seams good.", "green")

    def build(self) : 
        if self.mode == SET_VERSION :
            self.askVersion()
            return
        if self.state == ERROR :
            log.print("Cannot build " + self.name + " there was an error in configuration.", "red")
            return

        self.checkIncludesPaths()
        self.cleanIfNeeded()
        self.writeSettings()
        if self.release : 
            if self.versionAction == None :
                self.askVersion()
            else : 
                self.updateVersion()
            self.writeDependencies()
        try : 
            log.print("Start building " + self.name)
            self.compile()
            self.link()
            try : 
                self.makeExecutable(self.build_dir + os.sep + self.name)
            except :
                pass

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

    #call addToLibs inside but here the project is a dir with a lib.so and a version file
    #it's for tracking dependencies versions
    def addProject(self, proj) :
        if type(proj) == list or type(proj) == tuple :
            for s in proj :
                self.addProject(s)
            return
        versionfp = proj + os.sep + "version"
        if not os.path.exists(versionfp) :
            log.print("No version file in " + proj, "red")
            self.state = ERROR
            return

        version = ft.read(versionfp)
        self.dependencies[proj] = version
        for f in os.listdir(proj) :
            if ft.ext(f) == "a" or ft.ext(f) == "lib"  or ft.ext(f) == "so" :
                self.addToLibs(proj + os.sep + f)

    def writeDependencies(self) :
        if self.dependencies == {} :
            log.print("No dependencies found.", "yellow")
            return
        depthfp = self.build_dir + os.sep + "dependencies"
        ft.write(json.dumps(self.dependencies, indent=4), depthfp)

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
 
    def depthlist(self, src) :
        #get the dependencies
        cmd = [self.builder, "-MM", src]
        cmd.extend(self.listAsArgs(self.includes, "-I"))
        ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ls = ret.stdout.decode("utf-8")
        if platform.system() == "Windows" :
            pass
        else : 
            ls = ls.replace("\\", "")
        ls = ls.split("\n")
        try : 
            tmp = ls[0].split(":")[1]
            tmp = tmp.split(" ")
            ls = ls[1:]
            for t in tmp :
                if t == "" : continue
                ls.append(t)
        except : 
            pass
        return ls[:10]

    def depthmdtime(self, depthls) : 
        r = {}
        for d in depthls :
            for path in d.split(" ") : 
                if path == "" : continue
                try : 
                    r[path] = os.path.getmtime(path)
                except : 
                    log.print("Could not get mtime for " + path, "red")
        return r

    def needRebuild(self, src) : 
        log.print("Checking if " + src + " needs to be rebuilt...", "yellow")
        r = False
        if not os.path.exists(self.obj(src)) : 
            log.print("Detecting changed, .obj not found. (" + src + ")", "yellow")
            r = True
        current = ft.read(src)
        src_hash = hashlib.sha256(current.encode("utf-8")).hexdigest()
        cache_data = {}
        cache_data["src_hash"] = src_hash
        cache_data["depth"] = {}
        old_cached_data = {}
        old_cached_data["src_hash"] = ""
        old_cached_data["depth"] = {}
        depth = []
        if not os.path.exists(self.cache(src)) :
            r = True
            log.print("Detecting changed, .cache not found. (" + src + ")", "yellow")
            depth = self.depthlist(src)
            cache_data["depth"] = self.depthmdtime(self.depthlist(src))
        else : 
            old_cached_data = json.loads(ft.read(self.cache(src)))

        if src_hash != old_cached_data["src_hash"] and os.path.exists(self.cache(src)):
            r = True
            log.print("Detecting changed, src hash changed. (" + src + ")", "yellow")
            cache_data["depth"] = self.depthmdtime(self.depthlist(src))

        else : 
            diff = False
            changed = ""
            if not r : 
                for d in old_cached_data["depth"] :
                    if old_cached_data["depth"][d] != os.path.getmtime(d) :
                        if ("_gen.h" in d) : continue
                        diff = True
                        changed = d
                        cache_data["depth"] = self.depthmdtime(self.depthlist(src))
                        break
            if diff : 
                log.print("Detecting changed, one of the depth list mtime changed : " + changed + " -- (" + src + ")", "yellow")
                r = True

            if not diff and not r : 
                cache_data["depth"] = old_cached_data["depth"]
            if len(cache_data["depth"])==0 and len(old_cached_data["depth"]) != 0 :
                cache_data["depth"] = old_cached_data["depth"]

        try : 
            open(self.cache(src), "w").write(json.dumps(cache_data))
        except : 
            log.print("Could not write cache file for " + src, "red")
        if r : 
            log.print("Rebuilding " + src + " because it has changed.", "yellow")
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

    def addAllLibsInDir(self, dir) : 
        if not os.path.isdir(dir) :
            log.print("Directory of shared libraries not found : " + dir, "red")
            self.state = ERROR
            return
        self.addToLibDirs(dir)
        files = os.listdir(dir)
        for f in files :
            if ft.ext(f) == "so" or ft.ext(f) == "a" or ft.ext(f) == "lib" :
                self.addToLibs(dir + os.sep + f)

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
    #libname can alsoo be a path to a .pc file
    #OOOR a directory where there are .pc files
    def addInstalledLibrary(self, libname) : 
        def add_one(self, libname) :
            if os.sep in libname : 
                log.print ("Adding a .pc file from " + libname, "yellow")
                if not os.path.exists(libname) :
                    log.print("Could not find " + libname, "red")
                    return
            else :
                log.print("Adding " + libname + " from pkg-config.", "yellow")
            includes = []
            flags = []
            libs = []

            cmd = ["pkg-config", "--cflags", libname]
            ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _flags = ret.stdout.decode("utf-8")

            for f in _flags.split(" ") : 
                if f.startswith("-I") :
                    includes.append(f)
                elif f.startswith("-") : 
                    flags.append(f)

            cmd = ["pkg-config", "--libs", libname]
            ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _libs = ret.stdout.decode("utf-8")

            for l in _libs.split(" ") :
                if l.startswith("-l") :
                    libs.append(l)

            for i in includes : 
                if i not in self.includes :
                    self.includes.append(i)
            for f in flags :
                if f not in self.flags :
                    self.flags.append(f)
            for l in libs :
                if l not in self.libs :
                    self.libs.append(l)

        if not os.path.isdir(libname) :
            add_one(self, libname)
        else : 
            for f in os.listdir(libname) :
                if f.endswith(".pc") :
                    add_one(self, libname + os.sep + f)

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

    def createPackage(self) : 
        if not os.path.exists(self.packageSettings.rootDir): 
            log.print("The package root dir " + self.packageSettings.rootDir + " does not exist. Abort.", "red")
            return

        root = self.packageSettings.rootDir
        for f in self.packageSettings._toCopy : 
            log.print("Copying " + f[0], "yellow")
            if os.path.isdir(f[0]) :
                shutil.copytree(f[0], root + os.sep + f[1], dirs_exist_ok=True)
            else : 
                shutil.copy(f[0], root + os.sep + f[1])
        log.print("All files are copied and ready to be distributed.\nCreating the package now...", "green")

        to_compress = []
        for f in os.listdir(root) :
            if os.path.isdir(root + os.sep + f) :
                to_compress.append(f)
        os.chdir(root)
        cmd = ["/usr/bin/zip", "-r", ".." + os.sep + self.name + "." + self.lastVersion() + ".zip", "."]
        r = subprocess.run(cmd)
        if (r.returncode != 0) :
            log.print("Error while creating the package.\n(Error code : " + str(r.returncode)  + ")", "red")
        log.print("Package created and ready.", "green")
        log.print("Uploading the package on the server...", "yellow")
        if self.packageSettings.uploadDir == "" : 
            log.print ("The upload dir is empty, no upload will be done.", "orange")
            return
        if self.packageSettings.database == "" :
            log.print("No database filepath given, update the server package list can't be done.", "red")
            return
        
        os.chdir("..")
        shutil.copy(self.name + "." + self.lastVersion() + ".zip", self.packageSettings.uploadDir)
        log.print("Package uploaded.", "green")
        log.print("Updating the database...", "yellow")
        data = {}
        try : 
            data = json.loads(ft.read(self.packageSettings.database))
        except : 
            pass
        data[self.name] = {"version" : self.lastVersion()}
        ft.write(json.dumps(data), self.packageSettings.database)
        log.print("Database updated.", "green")

def create(name, argv=[], builder="g++") : 
    _r = Project(name)
    _r.builder = builder
    if len(argv) > 0 :
        _r.setFromArgs(argv)
    if platform.system() == "Windows" : 
        pass
    else : 
        _r.addToLibDirs(["/usr/local/lib", "/usr/lib", "/usr/lib/x86_64-linux-gnu"])
    return _r



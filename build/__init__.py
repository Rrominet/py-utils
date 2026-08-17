from ml import fileTools as ft
from ml import log
import os
import platform
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
import hashlib
import shlex

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
        self.symlink_lib_dirs = [] # custom dirs only; never mutate/scan system library dirs
        self.rpath_dirs = ["$ORIGIN", "$ORIGIN/../lib", "$ORIGIN/lib"]
        self.libs = [] # names
        self.libsPaths = []
        self.srcs = []
        self.modules = []
        self.definitions = [] # #define
        self.flags = ["pthread"] # -O3, -g, -pthread...
        self.raw_compile_flags = [] # raw multi-token/compiler flags from pkg-config
        self.link_flags = [] # raw linker-only flags (for example -Wl,... from pkg-config)
        self.futures = []
        self.max_workers = max(1, os.cpu_count() or 1)
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

    def _builderName(self) :
        return os.path.basename(self.builder)

    def _isEmscripten(self) :
        return self._builderName() in ("em++", "emcc")

    #type is debug or release
    def setType(self, type) :
        if type == debug and not self._isEmscripten() :
            self.flags += ["Og", "g", "-gsplit-dwarf"]
        elif type == debug and self._isEmscripten() :
            self.flags += [
                "O0",
                "-fexceptions",
                "-sASSERTIONS=2",
                "-g3",
                "-sEXCEPTION_DEBUG",
                "-sSTACK_OVERFLOW_CHECK=2",
                "-sNO_DISABLE_EXCEPTION_CATCHING",
            ]

        if type == debug :
            self.definitions += ["mydebug", "mldebug"]
        else :
            self.definitions.append("NDEBUG")

        if type == release and not self._isEmscripten() :
            self.flags.append("O3")
        elif type == release and self._isEmscripten() :
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

    def _sourceKey(self, srcfilepath) :
        # Basenames are not unique (src/foo.cpp and tests/foo.cpp used to collide).
        # Keep the filename readable and add a stable hash of the real source path.
        realpath = os.path.normcase(os.path.realpath(srcfilepath))
        digest = hashlib.sha1(realpath.encode("utf-8")).hexdigest()[:12]
        basename = os.path.basename(ft.noExt(srcfilepath))
        return basename + "." + digest

    def obj(self, srcfilepath) :
        return os.path.join(self.obj_dir, self._sourceKey(srcfilepath) + ".o")

    def depfile(self, srcfilepath) :
        return os.path.join(self.obj_dir, self._sourceKey(srcfilepath) + ".d")

    def module(self, srcfilepath) :
        return os.path.join(self.modules_dir, self._sourceKey(srcfilepath) + ".o")

    def cache(self, srcfilepath) :
        # Per-source cache now stores only the compile-command signature.
        # Dependencies themselves live in the compiler-generated .d file.
        return os.path.join(self.cache_dir, self._sourceKey(srcfilepath) + ".cmd")

    def linkCache(self) :
        return os.path.join(self.cache_dir, "link.cmd")

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
            if not f :
                continue
            if f[0] == "-" :
                l.append(f)
            else :
                l.append("-" + f)
        return l

    def _commandSignature(self, cmd) :
        # NUL separators avoid ambiguities that a normal string join can create.
        return hashlib.sha256("\0".join(cmd).encode("utf-8")).hexdigest()

    def _writeCommandSignature(self, filepath, cmd) :
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f :
            f.write(self._commandSignature(cmd))

    def _readCommandSignature(self, filepath) :
        try :
            with open(filepath, "r") as f :
                return f.read().strip()
        except OSError :
            return ""

    def compileCommand(self, srcfilepath, record=True) :
        cmd = [self.builder]
        if ft.ext(srcfilepath) == "c" :
            cmd += ["-x", "c"]

        if self.shared or self.outputType == SHARED_LIB :
            cmd += ["-c", "-fPIC", srcfilepath, "-o", self.obj(srcfilepath)]
        else :
            cmd += ["-c", srcfilepath, "-o", self.obj(srcfilepath)]

        # Generate the complete dependency list as a side effect of the real
        # compilation. This is much cheaper than running a separate `-MM`
        # preprocessing pass on every incremental build.
        cmd += [
            "-MMD",
            "-MF", self.depfile(srcfilepath),
            "-MT", os.path.basename(self.obj(srcfilepath)),
        ]

        cmd.extend(self.listAsArgs(self.includes, "-I"))
        cmd.extend(self.listAsArgs(self.definitions, "-D"))
        cmd.extend(self.flagsAsArgs(self.flags))
        cmd.extend(self.raw_compile_flags)

        if self.export_compile_commands and record :
            self.compile_commands.append({
                "directory" : self.build_dir,
                "command" : shlex.join(cmd),
                "file" : srcfilepath,
            })
        return cmd

    def _parseDepfile(self, filepath) :
        """Return dependencies from the first rule of a GCC/Clang .d file."""
        with open(filepath, "r") as f :
            text = f.read()

        # Join makefile continuation lines and read the first logical rule.
        text = text.replace("\\\r\n", "").replace("\\\n", "")
        first_rule = text.splitlines()[0] if text.splitlines() else ""
        if ":" not in first_rule :
            raise ValueError("Invalid dependency file: " + filepath)

        deps_text = first_rule.split(":", 1)[1]
        # GCC escapes spaces in filenames with backslashes. shlex handles that
        # correctly on the Unix-like toolchains this builder targets.
        deps = shlex.split(deps_text, posix=(platform.system() != "Windows"))
        return [d for d in deps if d]

    def _dependencyPath(self, path) :
        if os.path.isabs(path) :
            return os.path.normpath(path)
        return os.path.normpath(os.path.join(self.build_dir, path))

    def _statMtimeNs(self, path, stat_cache=None) :
        """stat() a path once per build, even if hundreds of TUs include it."""
        path = os.path.normcase(os.path.normpath(path))
        if stat_cache is not None and path in stat_cache :
            return stat_cache[path]
        try :
            value = os.stat(path).st_mtime_ns
        except OSError :
            value = None
        if stat_cache is not None :
            stat_cache[path] = value
        return value

    def needRebuild(self, src, cmd=None, stat_cache=None) :
        log.print("Checking if " + src + " needs to be rebuilt...", "yellow")
        obj = self.obj(src)
        depfile = self.depfile(src)
        cmdcache = self.cache(src)

        if cmd is None :
            cmd = self.compileCommand(src, record=False)

        obj_mtime = self._statMtimeNs(obj, stat_cache)
        if obj_mtime is None :
            log.print("Rebuilding: object not found. (" + src + ")", "yellow")
            return True

        if not os.path.isfile(depfile) :
            log.print("Rebuilding: dependency file not found. (" + src + ")", "yellow")
            return True

        if self._readCommandSignature(cmdcache) != self._commandSignature(cmd) :
            log.print("Rebuilding: compile command changed. (" + src + ")", "yellow")
            return True

        try :
            dependencies = self._parseDepfile(depfile)
        except Exception as e :
            log.print("Rebuilding: could not read dependency file for " + src + " (" + str(e) + ")", "yellow")
            return True

        # Some compilers/toolchains may omit the source from the dependency
        # rule in edge cases, so explicitly include it.
        dependencies.append(src)

        seen = set()
        for dep in dependencies :
            dep = self._dependencyPath(dep)
            key = os.path.normcase(dep)
            if key in seen :
                continue
            seen.add(key)

            dep_mtime = self._statMtimeNs(dep, stat_cache)
            if dep_mtime is None :
                log.print("Rebuilding: dependency disappeared: " + dep + " -- (" + src + ")", "yellow")
                return True
            if dep_mtime > obj_mtime and "_gen.h" not in dep :
                log.print("Rebuilding: dependency changed: " + dep + " -- (" + src + ")", "yellow")
                return True

        return False

    def compile(self) :
        log.print("Starting compilation...")
        os.makedirs(self.obj_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.compile_commands = []

        jobs = []
        stat_cache = {}
        for src in self.srcs :
            if os.path.basename(src) in self.srcs_exclude :
                log.print("Skipping " + os.path.basename(src) + " because it is in the exclude list.", "yellow")
                continue

            # Record compile_commands.json for every translation unit, even when
            # there is nothing to rebuild.
            cmd = self.compileCommand(src)
            if self.needRebuild(src, cmd, stat_cache=stat_cache) :
                jobs.append((src, cmd))
            else :
                log.print("No changes in " + src, "yellow")

        def make_job(src, cmd) :
            def comp() :
                log.print("Compiling " + src, "yellow")
                self.logCmd(cmd)
                ret = subprocess.run(cmd, cwd=self.build_dir).returncode
                if ret != 0 :
                    # Never allow a failed/partial compile to look up-to-date on
                    # the next run.
                    for filepath in (self.cache(src), self.obj(src), self.depfile(src)) :
                        try :
                            os.remove(filepath)
                        except OSError :
                            pass
                    raise RuntimeError("Compilation error with " + os.path.basename(src))

                self._writeCommandSignature(self.cache(src), cmd)
                log.print(os.path.basename(src) + " compiled.\n", "green")
            return comp

        self.exec([make_job(src, cmd) for src, cmd in jobs])

        if self.export_compile_commands :
            compile_commands_path = os.path.abspath(os.path.join(self.build_dir, "..", "compile_commands.json"))
            with open(compile_commands_path, "w") as f :
                json.dump(self.compile_commands, f, indent=2)

        if jobs :
            log.print(str(len(jobs)) + " translation unit(s) compiled.\n", "yellow")
        else :
            log.print("Compilation already up to date.\n", "green")
        return len(jobs) > 0

    def exec(self, funcs) :
        if not funcs :
            return

        if self.useThreads and len(funcs) > 1 :
            self.futures = []
            workers = min(self.max_workers, len(funcs))
            with ThreadPoolExecutor(max_workers=workers) as pool :
                self.futures = [pool.submit(fn) for fn in funcs]
                try :
                    for future in as_completed(self.futures) :
                        future.result()
                except Exception :
                    for future in self.futures :
                        future.cancel()
                    raise
        else :
            for fn in funcs :
                fn()

    def killCompile(self) :
        # Kept for API compatibility, but intentionally no longer used by the
        # builder. The old implementation used killall and could terminate
        # unrelated g++/cc1plus processes on the machine.
        log.print("killCompile() is deprecated; active build jobs are cancelled safely instead.", "orange")

    def logCmd(self, cmd) :
        log.print(shlex.join(cmd), "cyan")

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

    def outputPath(self) :
        if self.outputType == STATIC_LIB :
            return os.path.join(self.build_dir, "lib" + self.name + ".a")
        if self._isEmscripten() :
            return os.path.join(self.build_dir, self.name + ".js")
        return os.path.join(self.build_dir, self.getFileName())

    def _linkCommand(self) :
        if self.outputType == STATIC_LIB :
            cmd = ["ar", "rcs", self.outputPath()]
            for s in self.srcs :
                if os.path.basename(s) in self.srcs_exclude :
                    continue
                cmd.append(self.obj(s))
            return cmd

        cmd = [self.builder]
        if not self._isEmscripten() and shutil.which("mold") :
            cmd.append("-fuse-ld=mold")
        if self.shared or self.outputType == SHARED_LIB :
            cmd.append("-shared")
        cmd.extend(self.flagsAsArgs(self.flags))
        if self.static :
            cmd.extend(["-static", "-static-libgcc", "-static-libstdc++"])

        for s in self.srcs :
            if os.path.basename(s) in self.srcs_exclude :
                continue
            cmd.append(self.obj(s))

        cmd += ["-o", self.outputPath()]
        cmd.extend(self.libsPaths)
        cmd.extend(self.listAsArgs(self.lib_dirs, "-L"))
        cmd.extend(self.libsAsArgs())
        cmd.extend(self.link_flags)

        if self.rpath_dirs :
            cmd.append(self.rpathAsArgs())
        return cmd

    def _resolvedLibraryFiles(self) :
        """Best-effort list of linked library files for incremental relinking."""
        files = []
        for path in self.libsPaths :
            if os.path.exists(path) :
                files.append(path)

        for lib in self.libs :
            name = lib[2:] if lib.startswith("-l") else lib
            if os.path.isabs(name) and os.path.exists(name) :
                files.append(name)
                continue
            if name.startswith(":") :
                candidates = [name[1:]]
            elif ft.ext(name) in ("a", "so", "lib") :
                candidates = [name]
            else :
                candidates = ["lib" + name + ".a"] if self.static else ["lib" + name + ".so", "lib" + name + ".a"]

            found = False
            for directory in self.lib_dirs :
                for candidate in candidates :
                    path = os.path.join(directory, candidate)
                    if os.path.exists(path) :
                        files.append(path)
                        found = True
                        break
                if found :
                    break
        return files

    def needRelink(self, cmd=None) :
        if cmd is None :
            cmd = self._linkCommand()
        output = self.outputPath()

        if not os.path.exists(output) :
            log.print("Relinking: output not found.", "yellow")
            return True

        if self._readCommandSignature(self.linkCache()) != self._commandSignature(cmd) :
            log.print("Relinking: link command changed.", "yellow")
            return True

        try :
            output_mtime = os.stat(output).st_mtime_ns
        except OSError :
            return True

        inputs = []
        for src in self.srcs :
            if os.path.basename(src) not in self.srcs_exclude :
                inputs.append(self.obj(src))
        inputs.extend(self._resolvedLibraryFiles())

        for path in inputs :
            if not os.path.exists(path) :
                log.print("Relinking: link input missing: " + path, "yellow")
                return True
            if os.stat(path).st_mtime_ns > output_mtime :
                log.print("Relinking: link input changed: " + path, "yellow")
                return True

        return False

    def link(self) :
        if self.state == ERROR :
            raise RuntimeError("Cannot link " + self.name + ": there was an error in build.")

        self.createSharedLibsSymlinks()
        cmd = self._linkCommand()
        if not self.needRelink(cmd) :
            log.print("Linking already up to date.\n", "green")
            return False

        log.print("Starting linking process...")
        self.logCmd(cmd)

        # `ar rcs` updates/adds members but does not remove members that are no
        # longer in the project. Recreate static archives from scratch.
        if self.outputType == STATIC_LIB and os.path.exists(self.outputPath()) :
            os.remove(self.outputPath())

        ret = subprocess.run(cmd, cwd=self.build_dir).returncode
        if ret != 0 :
            try :
                os.remove(self.linkCache())
            except OSError :
                pass
            raise RuntimeError("Linking error")

        self._writeCommandSignature(self.linkCache(), cmd)
        log.print("Linking done.\n", "yellow")
        return True

    def getFileName(self) :
        if self.shared or self.outputType == SHARED_LIB :
            return "lib" + self.name + ".so"
        elif self.outputType == STATIC_LIB :
            return "lib" + self.name + ".a"
        else : 
            return self.name

    def clean(self) :
        log.print("Cleaning " + self.name + " project ...")
        for directory in (self.obj_dir, self.cache_dir, self.modules_dir) :
            shutil.rmtree(directory, ignore_errors=True)

        outputs = [self.outputPath()]
        if self._isEmscripten() :
            # Common Emscripten side outputs. Missing files are harmless.
            outputs += [
                os.path.join(self.build_dir, self.name + ".wasm"),
                os.path.join(self.build_dir, self.name + ".worker.js"),
            ]
        for filepath in outputs :
            try :
                os.remove(filepath)
            except OSError :
                pass

        os.makedirs(self.cache_dir, exist_ok=True)
        log.print("Cleaning done.\n", "green")

    def install(self) : 
        pass

    def makeExecutable(self, filepath) :
        if self._isEmscripten() or platform.system() == "Windows" :
            return
        if not os.path.exists(filepath) :
            return
        mode = os.stat(filepath).st_mode
        os.chmod(filepath, mode | 0o111)

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
            tocheck = inc[2:] if inc.startswith("-I") else inc
            if not os.path.isabs(tocheck) :
                tocheck = os.path.join(self.build_dir, tocheck)
            tocheck = os.path.normpath(tocheck)
            log.print("Checking include path " + tocheck, "yellow")
            if not os.path.exists(tocheck) :
                raise FileNotFoundError("The include path " + inc + " does not exist.")
            if not os.path.isdir(tocheck) :
                raise NotADirectoryError("The include path " + inc + " is not a directory.")

        log.print("Include paths seem good.", "green")

    def build(self) :
        if self.mode == SET_VERSION :
            self.askVersion()
            return
        if self.state == ERROR :
            raise RuntimeError("Cannot build " + self.name + ": there was an error in configuration.")

        self.checkIncludesPaths()
        os.makedirs(self.obj_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        if self.release :
            if self.versionAction is None :
                self.askVersion()
            else :
                self.updateVersion()
            self.writeDependencies()

        log.print("Start building " + self.name)
        self.compile()
        self.link()

        if self.outputType == PROGRAMM :
            self.makeExecutable(self.outputPath())

        log.print("Done.\nOutput is " + self.outputPath() + "\n", "green")

    #if the src is a file, it will be added to srcs
    #if the src is a directory, all of its contents will be added
    #if recursive is true, subdirectories are traversed too
    def addToSrcs(self, src, reccursive=False) :
        if isinstance(src, (list, tuple)) :
            for s in src :
                self.addToSrcs(s, reccursive)
            return

        src = os.path.abspath(src)
        if not os.path.exists(src) :
            raise FileNotFoundError("Source not found : " + src)

        if os.path.isdir(src) :
            for f in sorted(os.listdir(src)) :
                path = os.path.join(src, f)
                if os.path.isdir(path) :
                    if reccursive :
                        self.addToSrcs(path, True)
                    continue
                self.addToSrcs(path, reccursive)
            return

        ext = ft.ext(src)
        if ext.lower() in ("c", "cpp", "cc", "cxx") :
            if src not in self.srcs :
                self.srcs.append(src)
        elif ext == "ixx" :
            if src not in self.modules :
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
            lib = os.path.abspath(lib)
            if lib not in self.libsPaths :
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
 
    def _addLibDir(self, directory, add_rpath=False, create_symlinks=False) :
        directory = os.path.expanduser(directory)
        original = directory
        if not os.path.isabs(directory) :
            directory = os.path.abspath(os.path.join(self.build_dir, directory))
        directory = os.path.normpath(directory)

        if not os.path.isdir(directory) :
            self.state = ERROR
            log.print("Directory of shared libraries not found : " + directory, "red")
            return

        if directory not in self.lib_dirs :
            self.lib_dirs.append(directory)

        if add_rpath :
            if original.startswith("./") :
                rpath = "$ORIGIN" + original[1:]
            else :
                rpath = directory
            if rpath not in self.rpath_dirs :
                self.rpath_dirs.append(rpath)

        if create_symlinks and directory not in self.symlink_lib_dirs :
            self.symlink_lib_dirs.append(directory)

    def addToLibDirs(self, dir) :
        if isinstance(dir, (list, tuple)) :
            for s in dir :
                self.addToLibDirs(s)
            return
        self._addLibDir(dir, add_rpath=True, create_symlinks=True)

    def addAllLibsInDir(self, dir) :
        if not os.path.isdir(dir) :
            log.print("Directory of shared libraries not found : " + dir, "red")
            self.state = ERROR
            return
        self.addToLibDirs(dir)
        for f in os.listdir(dir) :
            if ft.ext(f) in ("so", "a", "lib") :
                self.addToLibs(os.path.join(dir, f))

    def createSharedLibsSymlinks(self) :
        # Only custom library directories are scanned. The old code scanned
        # /usr/lib and friends on every link and even attempted to create
        # symlinks there when permissions allowed it.
        for d in self.symlink_lib_dirs :
            self.createSharedLibsSymlinksInDir(d)

    def createSharedLibsSymlinksInDir(self, dir) :
        try :
            files = os.listdir(dir)
        except OSError :
            return
        for f in files :
            match = re.match(r"^(.*\.so)(?:\..+)$", f)
            if not match :
                continue
            linkpath = os.path.join(dir, match.group(1))
            if os.path.exists(linkpath) :
                continue
            try :
                os.symlink("./" + f, linkpath)
            except OSError :
                pass

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
        def add_one(self, name) :
            if os.sep in name :
                log.print("Adding a .pc file from " + name, "yellow")
                if not os.path.exists(name) :
                    log.print("Could not find " + name, "red")
                    self.state = ERROR
                    return
            else :
                log.print("Adding " + name + " from pkg-config.", "yellow")

            cflags_ret = subprocess.run(
                ["pkg-config", "--cflags", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if cflags_ret.returncode != 0 :
                self.state = ERROR
                raise RuntimeError("pkg-config --cflags failed for " + name + ": " + cflags_ret.stderr.strip())

            cflags = shlex.split(cflags_ret.stdout)
            i = 0
            while i < len(cflags) :
                flag = cflags[i]
                if flag == "-I" and i + 1 < len(cflags) :
                    inc = cflags[i + 1]
                    if inc not in self.includes :
                        self.includes.append(inc)
                    i += 2
                    continue
                if flag.startswith("-I") :
                    if flag not in self.includes :
                        self.includes.append(flag)
                elif flag not in self.raw_compile_flags :
                    self.raw_compile_flags.append(flag)
                i += 1

            libs_ret = subprocess.run(
                ["pkg-config", "--libs", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if libs_ret.returncode != 0 :
                self.state = ERROR
                raise RuntimeError("pkg-config --libs failed for " + name + ": " + libs_ret.stderr.strip())

            tokens = shlex.split(libs_ret.stdout)
            i = 0
            while i < len(tokens) :
                token = tokens[i]
                if token == "-L" and i + 1 < len(tokens) :
                    self._addLibDir(tokens[i + 1], add_rpath=False, create_symlinks=False)
                    i += 2
                    continue
                if token.startswith("-L") :
                    self._addLibDir(token[2:], add_rpath=False, create_symlinks=False)
                elif token.startswith("-l") :
                    if token not in self.libs :
                        self.libs.append(token)
                else :
                    # Preserve linker-only options such as -Wl,..., -pthread,
                    # -framework Foo, etc. Do not silently throw them away.
                    self.link_flags.append(token)
                i += 1

        if not os.path.isdir(libname) :
            add_one(self, libname)
        else :
            for f in sorted(os.listdir(libname)) :
                if f.endswith(".pc") :
                    add_one(self, os.path.join(libname, f))

    def setForModules(self) : 
        self.flags += ["-std=c++20", "-fmodules-ts"]
        self.useModules = True

    def makeSingleThreaded(self) : 
        self.useThreads = False

    def addEmiscriptenFlags(self) :
        self.flags += ["-sFETCH", "-sLLD_REPORT_UNDEFINED", "-lembind", "-std=c++17", "-fexceptions"]

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
        if not os.path.isdir(self.packageSettings.rootDir) :
            log.print("The package root dir " + self.packageSettings.rootDir + " does not exist. Abort.", "red")
            return

        root = os.path.abspath(self.packageSettings.rootDir)
        for source, dest in self.packageSettings._toCopy :
            log.print("Copying " + source, "yellow")
            destination = os.path.join(root, dest)
            if os.path.isdir(source) :
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else :
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.copy(source, destination)

        log.print("All files are copied and ready to be distributed.\nCreating the package now...", "green")
        archive = os.path.abspath(os.path.join(root, "..", self.name + "." + self.lastVersion() + ".zip"))
        cmd = ["/usr/bin/zip", "-r", archive, "."]
        r = subprocess.run(cmd, cwd=root)
        if r.returncode != 0 :
            raise RuntimeError("Error while creating the package. (Error code: " + str(r.returncode) + ")")

        log.print("Package created and ready.", "green")
        if self.packageSettings.uploadDir == "" :
            log.print("The upload dir is empty, no upload will be done.", "orange")
            return
        if self.packageSettings.database == "" :
            log.print("No database filepath given, update the server package list can't be done.", "red")
            return

        log.print("Uploading the package on the server...", "yellow")
        shutil.copy(archive, self.packageSettings.uploadDir)
        log.print("Package uploaded.", "green")
        log.print("Updating the database...", "yellow")
        data = {}
        try :
            data = json.loads(ft.read(self.packageSettings.database))
        except Exception :
            pass
        data[self.name] = {"version" : self.lastVersion()}
        ft.write(json.dumps(data), self.packageSettings.database)
        log.print("Database updated.", "green")


def create(name, argv=None, builder="g++") :
    if argv is None :
        argv = []
    _r = Project(name)
    _r.builder = builder
    if argv :
        _r.setFromArgs(argv)
    if platform.system() != "Windows" :
        # System search paths are linker search dirs, not project rpaths, and
        # certainly not directories where the builder should create symlinks.
        for directory in ("/usr/local/lib", "/usr/lib", "/usr/lib/x86_64-linux-gnu") :
            if os.path.isdir(directory) :
                _r._addLibDir(directory, add_rpath=False, create_symlinks=False)
    return _r


from ml import fileTools as ft
from ml import log
import os
import platform
import subprocess
import shutil
import json
import hashlib

debug = 1
release = 2

class JsProject : 
    def __init__(self, build_dir="") : 
        self.type = debug
        if build_dir == "" : 
            self.build_dir = os.getcwd()
        else : 
            self.build_dir = build_dir
        self.writtenFiles = []

        #gonna contains objects to be able to combine several files if wanted
        self.js = []
        self.css = []

        self.readWrittenFiles()

        #need to set this 
        #relative to build_dir
        self.html_tpl = ""

    def readWrittenFiles(self) : 
        if not os.path.exists(self.build_dir + os.sep + ".written_files") :
            return
        self.writtenFiles = ft.read(self.build_dir + os.sep + ".written_files").split("\n")

    def saveWrittenFiles(self) :
        data = ""
        for f in self.writtenFiles: 
            data += f + "\n"
        data = data[:-1]
        ft.write(data, self.build_dir + os.sep + ".written_files")

    #type is debug or release
    def setType(self, type) : 
        self.type = type

    def setFromArgs(self, args) : 
        if "release" in args : 
            self.setType(release)
        else : 
            self.setType(debug)

    def clean(self) : 
        log.print("Cleaning ...", "yellow")
        for f in self.writtenFiles :
            if os.path.exists(f) :
                log.print("Removing " + f, "yellow")
                os.remove(f)

        self.writtenFiles = []
        self.saveWrittenFiles()
        log.print("Cleaning done.\n", "green")

    def version(self) : 
        if not os.path.exists(self.build_dir + os.sep + "version") :
            return 0
        return int(ft.read(self.build_dir + os.sep + "version"))

    def setVersion(self, version) : 
        ft.write(str(version), self.build_dir + os.sep + "version")

    def incrementVersion(self):
        ft.write(self.version() + 1, self.build_dir + os.sep + "version")


    #if the src is a file, it will be added to js or css depending of its extension
    #if you give a list and a keyname, all the files will be bundle in one file at the end with the name of the keyname.
    #if the src is a directory, all of its contents will be added
    #if reccursive is true, the contents of subdirectories will be added
    def addFiles(self, src, keyname="") : 
        if type(src) == str :
            src = [src]

        if (len(src) == 0) : 
            raise Exception("JsProject.addFiles(src, keyname='', reccursive=False) : No src file given.")

        css = []
        js = []
        for s in src : 
            s = self.build_dir + os.sep + s
            if not os.path.exists(s) :
                raise Exception("JsProject.addFiles(src, keyname='', reccursive=False) : File not found : " + s)

            if os.path.isdir(s) : 
                files = os.listdir(s)
                for f in files :
                    if ft.ext(f) == "js" :
                        js.append(s + os.sep + f)
                    elif ft.ext(f) == "css" :
                        css.append(s + os.sep + f)
            else : 
                if ft.ext(s) == "js" :
                    js.append(s)
                elif ft.ext(s) == "css" :
                    css.append(s)

        if keyname == "" : 
            keyname = ft.baseName(src[0])

        if len(js) > 0 : 
            self.js.append({keyname : js})
        if len(css) > 0 : 
            self.css.append({keyname : css})

    #filepath is relative the project build dir
    #the hash will be automaticly added the the filename.
    def write(self, filepath, content) :
        log.print("Writing " + filepath, "yellow")
        _hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        log.print("Hash created : " + _hash, "yellow")
        relative_filepath = ft.parent(filepath) + os.sep + ft.baseName(filepath) + "." + _hash + "." + ft.ext(filepath)
        while(relative_filepath[0] == "/"): 
            relative_filepath = relative_filepath[1:]
        filepath = self.build_dir + os.sep + relative_filepath
        log.print("Absolute filepath : " + filepath, "yellow")
        self.writtenFiles.append(filepath)
        if (os.path.exists(filepath)): 
            log.print("File " + filepath + " didn't change, skipping.", "yellow")
            relative_filepath
        ft.write(content, filepath)
        log.print("File " + filepath + " written.", "green")
        return relative_filepath

    def compiledJs(self, files) : 
        log.print ("Compiling Js : " + "\n".join(files), "yellow")
        cmd = ["uglifyjs"]
        for f in files :
            cmd.append(f)
        cmd.append("-c")
        cmd.append("pure_funcs=['console.log']")
        cmd.append("-m")
        pcs = subprocess.run(cmd, capture_output=True, text=True)
        if (pcs.returncode != 0) :
            raise Exception("Js compilation failed for : " + "\n".join(files) + "\n" + pcs.stderr)
        return pcs.stdout

    def compiledCss(self, files) : 
        log.print ("Compiling Css : " + "\n".join(files), "yellow")
        cmd = ["cleancss"]
        cmd.append("-O2")
        for f in files :
            cmd.append(f)
        pcs = subprocess.run(cmd, capture_output=True, text=True)
        if (pcs.returncode != 0) :
            raise Exception("Css compilation failed for : " + "\n".join(files) + "\n" + pcs.stderr)
        return pcs.stdout

    def compile(self) : 
        _r = {"js" : [], "css" : []}
        for j in self.js : 
            for k in j :
                _r["js"].append({k : self.compiledJs(j[k])})

        for c in self.css : 
            for k in c :
                _r["css"].append({k : self.compiledCss(c[k])})

        return _r

    def build(self) : 
        if self.html_tpl == "" : 
            raise Exception("No html template set.")
        elif not os.path.exists(self.build_dir + os.sep + self.html_tpl) :
            raise Exception("Html template not found : " + self.html_tpl)

        self.clean()
        compiled = {"js" : [], "css" : []}
        if self.type == release: 
            log.print("Starting compilation...", "green")
            res = self.compile()
            log.print("Compilation succeed.", "green")
            log.print("Writing the builded files on disk...", "green")
            for f in res["js"] : 
                for k in f : 
                    file = self.write(k + ".js", f[k])
                    compiled["js"].append(file)
            for f in res["css"] : 
                for k in f : 
                    file = self.write(k + ".css", f[k])
                    compiled["css"].append(file)
            log.print("Files written.", "green")

        else : 
            for f in self.js :
                for k in f : 
                    for j in f[k] :
                        compiled["js"].append(j)
            for f in self.css :
                for k in f : 
                    for j in f[k] :
                        compiled["css"].append(j)
            log.print ("Debug mode : No compilation and write needed.", "yellow")
        
        htmlfile = self.html_tpl.replace("_tpl", "")
        log.print("Generating the html file " + htmlfile + "...", "green")
        self.generateHtml(htmlfile, compiled)
        log.print("Html file generated.", "green")
        self.saveWrittenFiles()
        log.print("Done.", "green")

    #filepath once again is relative to build_dir
    def generateHtml(self, filepath, compiled) :
        filepath = self.build_dir + os.sep + filepath
        htmls = ft.read(self. build_dir + os.sep + self.html_tpl)
        js = ""
        css = ""

        for j in compiled["js"] : 
            if not j : 
                continue
            js  += "<script src=\"" + j + "\" defer></script>"
            if self.type == debug : 
                js += "\n"

        for c in compiled["css"] : 
            if not c : 
                continue
            css += "<link rel=\"stylesheet\" href=\"" + c + "\">"
            if self.type == debug : 
                css += "\n"

        htmls = htmls.replace("*css*", css)
        htmls = htmls.replace("*js*", js)

        ft.write(htmls, filepath)
        self.writtenFiles.append(filepath)

    def install(self, dest) : 
        if not os.path.exists(dest) :
            raise Exception("No dest directory found. Can't install in : " + dest)

        htmlfile = ft.name(self.html_tpl.replace("_tpl", ""))
        installed = os.listdir(dest)
        for f in installed : 
            if ".html" not in f and ".css" not in f and ".js" not in f :
                continue
            already = False
            if f == htmlfile :
                log.print ("Removing " + dest + os.sep + f, "yellow")
                os.remove(dest + os.sep + f)
                continue

            for lf in self.writtenFiles :
                if f == ft.name(lf) : 
                    already = True
                    continue
            if (already) : 
                continue

            log.print ("Removing " + dest + os.sep + f, "yellow")
            os.remove(dest + os.sep + f)

        for f in self.writtenFiles : 
            if os.path.exists(dest + os.sep + ft.name(f)) :
                log.print("File " + ft.name(f) + " didn't change, skipping.", "yellow")
                continue
            log.print("Copying " + f + " to " + dest + os.sep + ft.name(f), "yellow")
            shutil.copy(f, dest + os.sep + ft.name(f))

def create(argv=[], build_dir="") : 
    _r = JsProject(build_dir)
    if len(argv) > 0 :
        _r.setFromArgs(argv)
    return _r



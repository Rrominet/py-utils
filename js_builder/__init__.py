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
        self._name = ""
        self._description = ""
        self.pwa = False

        #add files here you want to install that are not in the build for whatever reason
        self.toInstall = []
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

    def variable(self, name): 
        if(getattr(self, "_" + name) == "") :
            if os.path.exists(self.build_dir + os.sep + name) :
                setattr(self, "_" + name, ft.read(self.build_dir + os.sep + name))
        return getattr(self, "_" + name)

    def saveVariable(self, name, value): 
        setattr(self, "_" + name, value)
        ft.write(getattr(self, "_" + name), self.build_dir + os.sep + name)
        return getattr(self, "_" + name)

    def name(self): 
        return self.variable("name")
    def saveName(self, name) :
        return self.saveVariable("name", name)

    def description(self):
        return self.variable("description")
    def saveDescription(self, name) :
        return self.saveVariable("description", name)

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
        if "pwa" in args: 
            self.pwa = True

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
        versinstr = ft.read(self.build_dir + os.sep + "version")
        if (versinstr == "") :
            return 0
        try : 
            return int(versinstr)
        except :
            return 0

    def setVersion(self, version) : 
        ft.write(str(version), self.build_dir + os.sep + "version")

    def incrementVersion(self):
        ft.write(str(self.version() + 1), self.build_dir + os.sep + "version")

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
            log.print("Incrementing version... (current : " + str(self.version()) + ")", "yellow")
            self.incrementVersion()
            log.print("Version incremented : " + str(self.version()), "green")

        else : 
            for f in self.js :
                for k in f : 
                    for j in f[k] :
                        compiled["js"].append(j.replace(self.build_dir + os.sep, ""))
            for f in self.css :
                for k in f : 
                    for j in f[k] :
                        compiled["css"].append(j.replace(self.build_dir + os.sep, ""))
            log.print ("Debug mode : No compilation and write needed.", "yellow")
        
        htmlfile = self.html_tpl.replace("_tpl", "")
        log.print("Generating the html file " + htmlfile + "...", "green")
        self.generateHtml(htmlfile, compiled)
        log.print("Html file generated.", "green")
        self.saveWrittenFiles()
        if self.pwa : 
            self.buildPWA()

        log.print("Done.", "green")

    def buildPWA(self) :
        self.generateIcon()
        self.createPWAManifest()
        self.createPWAServiceWorkerFile()

        log.print("PWA files generated.", "green")

    def generateIcon(self) : 
        if os.path.exists(self.build_dir + os.sep + "images" + os.sep + "512.png") :
            log.print("Icon already exist. No need to generate it again.", "green")
            return
        path = input("Enter the path to your app icon : ")
        cmd = ["magick", path, "-resize", "512x512", self.build_dir + os.sep + "images" + os.sep + "512.png"] 
        log.print("Generating the icon...", "yellow")
        log.print ("Command : " + " ".join(cmd), "yellow")
        subprocess.run(cmd)
        if (os.path.exists(self.build_dir + os.sep + "images" + os.sep + "512.png")) :
            log.print("Icon generated.", "green")
        else : 
            log.print("Icon generation failed.", "red")

    def createPWAManifest(self) : 
        s ="""
{
  "name": "*name*",
  "description": "*description*",
  "icons": [
    {
      "src": "images/512.png",
      "type": "image/png",
      "sizes": "512x512"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "background_color": "#222222",
  "theme_color": "#222222"
}
        """

        if (self.name() == "") : 
            self.saveName(input("Missing a Name for you App, What is it : "))

        if (self.description() == "") : 
            self.saveDescription(input("Missing a Description for you App, What is it : "))

        s = s.replace("*name*", self.name().replace("\n", ""))
        s = s.replace("*description*", self.description().replace("\n", "\\n"))

        ft.write(s, self.build_dir + os.sep + "manifest.json")
        log.print("Manifest generated.", "green")

    def getPWACacheFiles(self) : 
        files = ["./"]
        tmp_files = ft.hierarchie(os.path.abspath(self.build_dir))
        for f in tmp_files:
            if os.path.isdir(f) : continue
            if ft.ext(f) == "php" : continue
            if ft.ext(f) == "py" : continue
            if ft.ext(f) == "" : continue
            if "README.md" in f : continue
            if ".written_files" in f : continue
            if "frameworks" in f : continue
            if "generate" in f : continue
            if "version" in f : continue
            if ".git" in f : continue
            if ("Node" in f) : continue
            if ("libs" in f) : continue
            if ("doc" in f) : continue
            if "index_tpl.html" in f : continue
            if "make" in f : continue
            f = f.replace(os.path.abspath(".") + os.sep, "")
            f = f.replace(os.sep, "/")
            files.append(f)
        r = "["
        for f in files : 
            r += "\"" + f + "\",\n"
        r += "]"
        return r;

    def defaultSW(self) :
        return """
// This is file is generated, don't edit it.
const version = *version*;
const cached = *cache-list*;
const cache_name = "cache";
async function oninstall()
{
    const cache = await caches.open(cache_name);
    return cache.addAll(cached);
}
self.addEventListener("install", (event) => 
    {
        event.waitUntil(oninstall());
    });
async function cacheFirst(request) 
{
    const cachedResponse = await caches.match(request);
    if (cachedResponse)
        return cachedResponse;
    try
    {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(cache_name);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        return Response.error();
    }
}
self.addEventListener("fetch", (event) =>
    {
        if (event.request.method != "GET")
            {
                // this let the browser handle the request normally.
                return;
            }
        const url = new URL(event.request.url);
        event.respondWith(cacheFirst(event.request));
    });
        """

    def createPWAServiceWorkerFile(self): 
        sw = self.defaultSW()
        sw = sw.replace("*cache-list*", self.getPWACacheFiles())
        sw = sw.replace("*version*", str(self.version()))
        ft.write(sw, self.build_dir + os.sep + "sw.js")
        log.print("Service worker file generated : " + self.build_dir + os.sep + "sw.js", "green")

    #filepath once again is relative to build_dir
    def generateHtml(self, filepath, compiled) :
        filepath = self.build_dir + os.sep + filepath
        htmls = ft.read(self. build_dir + os.sep + self.html_tpl)
        js = ""
        css = ""

        if self.pwa : 
            js +="""<script>if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js")</script>"""
        for j in compiled["js"] : 
            if not j : 
                continue
            js  += "<script src=\"" + j + "\" defer></script>"
            if self.type == debug : 
                js += "\n"

        if self.pwa : 
            css +=" <link rel='manifest' href='./manifest.json' />"

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
            if (self.pwa) : 
                self.toInstall.append("./manifest.json")
                self.toInstall.append("./sw.js")
                self.toInstall.append("./images/512.png")
            for f in self.toInstall : 
                if os.path.isdir(f) :
                    log.print("Copying " + f + " to " + dest + os.sep + f, "yellow")
                    shutil.copytree(f, dest + os.sep + f, dirs_exist_ok=True)
                else :
                    log.print("Copying " + f + " to " + dest + os.sep + f, "yellow")
                    shutil.copy(f, dest + os.sep + f)
        log.print("installed.", "green")

def create(argv=[], build_dir="") : 
    _r = JsProject(build_dir)
    if len(argv) > 0 :
        _r.setFromArgs(argv)
    return _r



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

class AppPage : 

    #opts need to have at least the key "url" (from the root like /about /contact, etc)
    #a key "title"
    # and optional : 
    #key "description"
    #key "image"
    #key "type" (article, website, etc...)
    #key "datePublished" and "dateModified"
#  "author": {
#    "@type": "Person",
#    "name": "Romain",
#    "url": "https://motion-live.com/about"
#  },
#  "publisher": {
#    "@type": "Organization",
#    "name": "Motion Live",
#    "logo": {
#      "@type": "ImageObject",
#      "url": "https://motion-live.com/img/logo.png"
#    }
#  },
    #if missing_keys is not empty, none of the operation can be done and a error message via log module is printed.
    def __init__(self, opts = {}, content="") : 
        self.missing_keys = []

        self.content = content
        if "content" in opts and content == "" :
            self.content = opts["content"]

        log.print("Trying to read : " + self.content[0:50], "yellow")
        if os.path.exists(self.content) : 
            self.content = ft.read(self.content)
        else : 
            log.print("File " + self.content[0:50] + " not found. Considered as pure text.", "yellow")

        self._level = -1
        if "url" not in opts:
            self.missing_keys.append("url")
        if "title" not in opts:
            self.missing_keys.append("title")
        if self.missing_keys:
            log.print("AppPage missing keys : " + ", ".join(self.missing_keys), "red")
        self.opts = opts

    def filepath(self) : 
        f = self.opts["url"]
        if ft.ext(f) == "" : 
            return f + "/index.html"
        return f

    def level(self) : 
        if self._level == -1 : 
            url = self.opts.get("url", "")
            if url == "" :
                return 0
            url = url.replace("//", "/")
            if url == "/" : 
                self._level = 0
            else : 
                self._level = url.count("/")
        return self._level

    def levelPrefix(self) : 
        prefix = "./"
        for i in range(self._level) : 
            prefix += "../"
        return prefix

    #this return the different meta tag needed for good sharing preview on social media like Facebook, Twitter, Discord, Line, What'sapp, etc
    # it's generated from the opts
    # it does the standars ones, the og ones and the twitter ones
    # it return a full html string that would be an index.html for this page. With an empty body.
    # use the log module to print messages
    def generatedMeta(self, global_organization=None) : 
        url = self.opts.get("url", "")
        title = self.opts.get("title", "")
        description = self.opts.get("description", "")
        image = self.opts.get("image", "")
        og_type = self.opts.get("type", "website")


        log.print("Generating html for page : " + url, "yellow")

        meta = ""
        meta += "<meta charset=\"UTF-8\">\n"
        meta += "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        meta += "<link rel=\"icon\" type=\"image/x-icon\" href=\"" + self.levelPrefix() + "favicon.ico\">\n"
        if title:
            meta += "<title>" + title + "</title>\n"
            meta += "<meta name=\"title\" content=\"" + title + "\">\n"
        if description:
            meta += "<meta name=\"description\" content=\"" + description + "\">\n"

        # og tags
        meta += "<meta property=\"og:type\" content=\"" + og_type + "\">\n"
        if url:
            meta += "<meta property=\"og:url\" content=\"" + url + "\">\n"
        if title:
            meta += "<meta property=\"og:title\" content=\"" + title + "\">\n"
        if description:
            meta += "<meta property=\"og:description\" content=\"" + description + "\">\n"
        if image:
            meta += "<meta property=\"og:image\" content=\"" + image + "\">\n"

        # twitter tags
        meta += "<meta name=\"twitter:card\" content=\"summary_large_image\">\n"
        if url:
            meta += "<meta name=\"twitter:url\" content=\"" + url + "\">\n"
        if title:
            meta += "<meta name=\"twitter:title\" content=\"" + title + "\">\n"
        if description:
            meta += "<meta name=\"twitter:description\" content=\"" + description + "\">\n"
        if image:
            meta += "<meta name=\"twitter:image\" content=\"" + image + "\">\n"

        json_type = self.opts.get("type", "Website")
        json_type = json_type.capitalize()

        json_ld = {}
        json_ld["@context"] = "https://schema.org"
        json_ld["@type"] = json_type
        json_ld["url"] = url
        json_ld["title"] = title
        json_ld["name"] = title
        json_ld["headline"] = title
        json_ld["description"] = description

        if "datePublished" in self.opts :
            json_ld["datePublished"] = self.opts["datePublished"]
        if "dateModified" in self.opts :
            json_ld["dateModified"] = self.opts["dateModified"]

        if "author" in self.opts :
            json_ld["author"] = self.opts["author"]
        if "publisher" in self.opts :
            json_ld["publisher"] = self.opts["publisher"]

        meta += "<script type=\"application/ld+json\">" + json.dumps(json_ld) + "</script>\n"
        if global_organization :
            global_organization["@context"] = "https://schema.org"
            meta += "<script type=\"application/ld+json\">" + json.dumps(global_organization) + "</script>\n"

        return meta

    def priority(self) : 
        return self.opts.get("priority", 0.5)

    def changefreq(self) : 
        return self.opts.get("changefreq", "monthly")

class JsProject : 
    def __init__(self, build_dir="", root_url="") : 
        self.type = debug
        self.root_url = root_url
        if self.root_url.endswith("/") : 
            self.root_url = self.root_url[:-1]
        self._name = ""
        self._description = ""
        self.pwa = False

        #add files here you want to install that are not in the build for whatever reason
        self.toInstall = []

        #add the files here you don't want to pwa to cache in advance
        self.nocache = []

        #list of AppPage objects
        self.app_pages = []
        self.app_pages_errors = []

        #list of root folder that gonna be linked in children apges
        #if non-existent, ignored.
        self.root_folders = ["js", "css", "images", "videos", "data", "fonts", "frameworks"]

        #urls from the root with the first "/" !
        self.disallowed_indexed = []

        #for a root site that have more than one site map in subdirs
        self.more_sitemaps = []

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

        self.global_author = None
        self.global_publisher = None
        self.global_organization = None

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
        
        if len(self.app_pages) == 0 : 
            htmlfile = self.html_tpl.replace("_tpl", "")
            log.print("Generating the html file " + htmlfile + "...", "green")
            self.generateHtml(htmlfile, compiled)
            log.print("Html file generated.", "green")
        else : 
            self.generatePages(compiled)

        self.saveWrittenFiles()
        if self.pwa : 
            self.buildPWA(self.nocache)

        self.generateRobotsTxt()
        self.generateSitemap()
        self.generateLlm()
        log.print("Done.", "green")

    def buildPWA(self, filesToNotCache=[]) :
        self.generateIcon()
        self.createPWAManifest()
        self.createPWAServiceWorkerFile(filesToNotCache)

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

    def getPWACacheFiles(self, filesToNotCache=[]) : 
        print(filesToNotCache)
        files = ["./"]
        tmp_files = ft.hierarchie(os.path.abspath(self.build_dir), True, [], True)
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
            if "llm.txt" in f : continue
            if "llms.txt" in f : continue
            if "sitemap.xml" in f : continue
            if "robots.txt" in f : continue
            if "__pycache__" in f : continue

            ignore = False
            for f2 in filesToNotCache :
                if os.path.isdir(f2) : 
                    if f2 in ft.parent(f) : 
                        ignore = True
                        continue
                if os.path.exists(f2) :
                    if f2.startswith("./") :
                        f2 = f2.replace("./", "")
                    if f.startswith("./") :
                        f = f.replace("./", "")
                    if f2 == f.replace(self.build_dir + os.sep, "") :
                        ignore = True
                        continue
            if ignore : 
                continue
            f = f.replace(os.path.abspath(".") + os.sep, "")
            f = f.replace(os.sep, "/")
            files.append(f)
        r = "["
        for f in files : 
            r += "\"" + f.replace("\"", "\\\"") + "\",\n"
        r += "]"
        return r;

    def defaultSW(self) :
        return """// This is file is generated, don't edit it.
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
        if (event.request.method != "GET"){return;}
        event.respondWith(cacheFirst(event.request));
    });
        """

    def createPWAServiceWorkerFile(self, filesToNotCache=[]) : 
        sw = self.defaultSW()
        sw = sw.replace("*cache-list*", self.getPWACacheFiles(filesToNotCache))
        sw = sw.replace("*version*", str(self.version()))
        ft.write(sw, self.build_dir + os.sep + "sw.js")
        log.print("Service worker file generated : " + self.build_dir + os.sep + "sw.js", "green")

    #filepath once again is relative to build_dir
    def generateHtml(self, filepath, compiled, meta="", content="", level=0) :
        prefix = "./"
        for i in range(level) : 
            prefix += "../"

        filepath = self.build_dir + os.sep + filepath
        htmls = ft.read(self. build_dir + os.sep + self.html_tpl)
        js = ""
        css = ""

        if self.pwa : 
            js +="<script>if ('serviceWorker' in navigator) navigator.serviceWorker.register('" + prefix + "sw.js')</script>"
        for j in compiled["js"] : 
            if not j : 
                continue
            js  += "<script src=\"" + prefix + j + "\" defer></script>"
            if self.type == debug : 
                js += "\n"

        if self.pwa : 
            css +=" <link rel='manifest' href='" + prefix + "manifest.json' />"

        for c in compiled["css"] : 
            if not c : 
                continue
            css += "<link rel=\"stylesheet\" href=\"" + prefix + c + "\">"
            if self.type == debug : 
                css += "\n"

        htmls = htmls.replace("*css*", css)
        htmls = htmls.replace("*js*", js)
        htmls = htmls.replace("*meta*", meta)
        htmls = htmls.replace("*content*", content)

        if not os.path.isdir(ft.parent(filepath)) :
            os.makedirs(ft.parent(filepath), exist_ok=True)

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
            try :
                log.print("Copying " + f + " to " + dest + os.sep + f.replace(self.build_dir + os.sep, ""), "yellow")
                self.installFile(f, dest + os.sep + f.replace(self.build_dir + os.sep, ""))
            except : 
                log.print("Error while copying " + f + " to " + dest + os.sep + f.replace(self.build_dir + os.sep, ""), "yellow")

        if (self.pwa) : 
            self.toInstall.append("./manifest.json")
            self.toInstall.append("./sw.js")
            self.toInstall.append("./images/512.png")
        if os.path.exists(self.build_dir + os.sep + "/robots.txt") :
            self.toInstall.append("./robots.txt")
        if os.path.exists(self.build_dir + os.sep + "/sitemap.xml") :
            self.toInstall.append("./sitemap.xml")
        if os.path.exists(self.build_dir + os.sep + "/llms.txt") :
            self.toInstall.append("./llms.txt")
        if os.path.exists(self.build_dir + os.sep + "/favicon.ico") :
            self.toInstall.append("./favicon.ico")

        for f in self.toInstall : 
            if os.path.isdir(f) :
                log.print("Copying " + f + " to " + dest + os.sep + f, "yellow")
                self.installDir(f, dest + os.sep + f)
            else :
                log.print("Copying " + f + " to " + dest + os.sep + f, "yellow")
                if not os.path.isdir(ft.parent(dest + os.sep + f)) :
                    os.makedirs(ft.parent(dest + os.sep + f))
                self.installFile(f, dest + os.sep + f)

        log.print("Installing " + str(len(self.app_pages)) + " pages...", "yellow")
        for p in self.app_pages :
            if p.opts["url"] == "/" : 
                continue
            fp = self.build_dir + os.sep + p.filepath()
            if ft.ext(fp) != "" : 
                fp = ft.parent(fp)
            if not os.path.isdir(fp) :
                log.print("The directory for page " + fp + " doesn't exist, can't install it.", "red")
                continue
            dst = dest + os.sep + fp.replace(self.build_dir, "")
            log.print("Installing " + fp + " to " + dst, "yellow")
            try : 
                self.installDir(fp, dst)
            except Exception as e :
                log.print("Error during copy :" + str(e), "yellow") 

        log.print("installed.", "green")

    def installFile(self, src, dest) : 
        if os.path.exists(src) and os.path.exists(dest) and os.path.getsize(src) == os.path.getsize(dest) :
            return
        if not os.path.isdir(ft.parent(dest)) :
            os.makedirs(ft.parent(dest))
        shutil.copy(src, dest)

    def installDir(self, src, dest) : 
        if not os.path.exists(dest) :
            os.makedirs(dest)
        for root, dirs, files in os.walk(src) :
            rel = root.replace(src, "")
            if rel.startswith(os.sep) :
                rel = rel[1:]
            dest_root = dest if rel == "" else dest + os.sep + rel
            if not os.path.isdir(dest_root) :
                os.makedirs(dest_root)
            filesndirs = dirs + files
            for f in filesndirs :
                s = root + os.sep + f
                d = dest_root + os.sep + f
                log.print("Copying " + s + " to " + d, "yellow")
                if os.path.islink(s) :
                    log.print("Creating symlink " + s + " to " + d, "yellow")
                    if os.path.exists(d) :
                        log.print("Symlink " + d + " already exists, skipping.", "yellow")
                        continue
                    try :
                        linkto = os.readlink(s)
                        os.symlink(linkto, d)
                        log.print("Symlink created.", "green")
                    except Exception as e :
                        log.print("Error while creating symlink " + s + " to " + d + " : " + str(e), "red")
                    continue
                if os.path.isdir(s) :
                    continue
                self.installFile(s, d)

    def addMissingOptsToPageOpts(self, opts) : 
        if not "author" in opts and self.global_author :
            opts["author"] = self.global_author
        if not "publisher" in opts and self.global_publisher :
            opts["publisher"] = self.global_publisher

    def addPage(self, opts, content="") : 
        self.addMissingOptsToPageOpts(opts)
        self.app_pages.append(AppPage(opts, content))

    #data is a json array
    def createPagesFromData(self, data) : 
        for p in data : 
            self.addMissingOptsToPageOpts(p)
            self.app_pages.append(AppPage(p))

    def createPagesFromFile(self, filepath) : 
        try: 
            data = ft.read(filepath)
            data = json.loads(data)
            self.createPagesFromData(data)
        except Exception as e : 
            log.print("Couldn't create the pages from the filepath : " + filepath, "red")
            log.print("More infos :", "red")
            log.print(str(e), "red")

    def createRootFolderLinks(self, directory, level=1) : 
        if not os.path.isdir(self.build_dir + os.sep + directory) : 
            log.print(directory + " is not a directory, skipping.", "yellow")
            return
        if directory == self.build_dir : 
            log.print(directory + " is the build directory, skipping.", "yellow")
            return
        if os.path.abspath(directory) == os.path.abspath(self.build_dir) :
            log.print(directory + " is the build directory, skipping.", "yellow")
            return
        if os.path.abspath(directory) == os.path.abspath(os.getcwd()) :
            log.print(directory + " is the current directory, skipping.", "yellow")
            return

        for f in os.listdir(self.build_dir + os.sep + directory) :
            if os.path.islink(self.build_dir + os.sep + directory + os.sep + f) :
                log.print("Removing " + self.build_dir + os.sep + directory + os.sep + f, "yellow")
                os.remove(self.build_dir + os.sep + directory + os.sep + f)
        
        prefix = ""
        for i in range(level) : 
            prefix += ".." + os.sep

        for f in self.root_folders : 
            if not os.path.exists(self.build_dir + os.sep + f) :
                continue
            log.print("Creating symlink " + prefix + f + " in " + self.build_dir + directory + os.sep + f, "yellow") 
            if not os.path.exists(self.build_dir + directory + os.sep + f) :
                try : 
                    os.symlink(prefix + f, self.build_dir + directory + os.sep + f)
                except Exception as e :
                    log.print("Couldn't create the symlink " + prefix + f + " in " + self.build_dir + directory + os.sep + f, "red")
                    log.print("More infos :", "red")
                    log.print(str(e), "red")
            else : 
                log.print(directory + os.sep + f + " already exist, skipping.", "yellow")

    def generatePages(self, compiled) : 
        self.app_pages_errors = []
        log.print("Generating pages...")
        for p in self.app_pages : 
            if len(p.missing_keys) > 0 : 
                log.print("Error in generating page :", "red")
                log.print("Missing keys :", "red")
                for k in p.missing_keys :
                    log.print("- " + k, "red")
                continue
            filepath = p.filepath()
            self.createRootFolderLinks(ft.parent(filepath), p.level())
            self.generateHtml(filepath, compiled, p.generatedMeta(self.global_organization), p.content, p.level())
        log.print("Pages generated", "green")

    def generateRobotsTxt(self) : 
        if self.root_url == "" :
            log.print("root_url is empty, mendatory for robots.txt to be generated.", "red")

        log.print("Generating robots.txt...")
        txt = """User-agent: *
"""
        for forbid in self.disallowed_indexed : 
            txt += "Disallow: " + forbid + "\n"
        txt += """
Allow: /
Sitemap: """ + self.root_url + """/sitemap.xml"""
        for sitemap in self.more_sitemaps : 
            txt +="\nSitemap: " + self.root_url + "/" + sitemap + "\n"

        log.print("robots.txt generated", "green")
        ft.write(txt, self.build_dir + os.sep + "robots.txt")

    def generateSitemap(self) : 
        log.print("Generating sitemap.xml...", "yellow")
        txt = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        txt += "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        for p in self.app_pages :
            txt += "<url>\n"
            url = self.root_url + p.opts["url"]
            url = url.replace("//", "/")
            txt += "<loc>" + url + "</loc>\n"
            txt += "<priority>" + str(float(p.priority())) + "</priority>\n"
            txt += "<changefreq>" + p.changefreq() + "</changefreq>\n"
            txt += "</url>\n"
        txt += "</urlset>"
        ft.write(txt, self.build_dir + os.sep + "sitemap.xml")
        log.print("sitemap.xml generated", "green")

    def indexPage(self) : 
        for p in self.app_pages : 
            if p.opts["url"] == "/" : 
                return p
        return None

    def generateLlm(self) : 
        if os.path.exists(self.build_dir + os.sep + "llm.txt") :
            os.remove(self.build_dir + os.sep + "llm.txt")

        log.print("Generating llms.txt...", "yellow")
        indpge = self.indexPage()
        if not indpge :
            log.print("No index page found for llms.txt, skipping.", "yellow")
            return
        txt = "# " + indpge.opts["title"] + "\n\n"
        txt += ">" + indpge.opts["description"] + "\n\n"
        txt += "## Core Pages\n\n"
        for p in self.app_pages : 
            if p.opts["url"] == "/" : 
                continue
            txt += "- [" + p.opts["title"] + "](" + p.opts["url"] + ") " + p.opts["description"] + "\n"

        ft.write(txt, self.build_dir + os.sep + "llms.txt")
        log.print("llms.txt generated", "green")

def create(argv=[], build_dir="", root_url="") : 
    _r = JsProject(build_dir, root_url)
    if len(argv) > 0 :
        _r.setFromArgs(argv)
    return _r



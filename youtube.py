from __future__ import unicode_literals
import os

libs = os.path.abspath(os.path.dirname(__file__))
libs += os.sep + ".." + os.sep + "libs"

frameworks = os.path.abspath(os.path.dirname(__file__))

import subprocess
import json
import sys
sys.path.append(libs)
sys.path.append(frameworks)

import youtube_dl
import ffmpeg
import requests

class Video : 
    def __init__(self, id, title) : 
        self.id = id
        self.title = title
        self.thumnailURL = "https://img.youtube.com/vi/" + self.id + "/hqdefault.jpg"
        self.videoURL = "https://youtu.be/" + self.id
        self.process = None
        self.onDownloading = []
        self.onFinished = []
        self.onError = []
        self.infos = ""
        self.downloading = False
        self.downloaded = False
        self.proxied = False
        self.proxying = False
        self.local = ""

    def download(self, outputdir) : 
        if self.findLocal(outputdir) : 
            return self.local
        def f(data) : 
            if (data["status"] == "downloading") : 
                self.downloading = True
                self.infos = "Downloading..."
                for f2 in self.onDownloading : 
                    f2(data)
            elif (data["status"] == "finished") : 
                self.downloading = False
                self.downloaded = True
                self.infos = "Finished."
                for f2 in self.onFinished : 
                    f2(data)
            elif (data["status"] == "error") : 
                self.downloading = False
                self.infos = "Error..."
                for f2 in self.onError : 
                    f2(data)

        with youtube_dl.YoutubeDL({"outtmpl" : outputdir + os.sep + self.title, 
            "progress_hooks" : [ f ], 
            "nocheckcertificate" : True}) as ydl : 
            ydl.download([self.videoURL])

        return self.findLocal(outputdir)

    def getSound(self, outputdir) : 
        f = self.download(outputdir)
        self.downloading = True
        self.infos = "Converting to .wav..."
        converter = ffmpeg.Ffmpeg()
        res = converter.wav(f)
        os.remove(f)
        self.infos = "Conversion finished."
        self.downloading = False
        return res

    def findLocal(self, outputdir) : 
        files = os.listdir(outputdir)
        for f in files : 
            if ( ".mp4" in f or ".mkv" in f or ".webm" in f ) and self.title in f : 
                self.local = outputdir + os.sep + f
                self.downloaded = True
                return self.local
        return None

    def findProxy(self, outputdir) : 
        self.findLocal(outputdir)
        if not self.local : 
            return ""
        proxy = self.local.replace(".mp4", "_proxy.avi")
        proxy = proxy.replace(".mkv", "_proxy.avi")
        proxy = proxy.replace(".webm", "_proxy.avi")

        if os.path.exists(proxy) : 
            self.downloaded = True
            self.proxied = True
            return proxy
        return None

    def findSound(self, outputdir) : 
        self.findLocal(outputdir)
        if not self.local : 
            return ""
        wav = self.local.replace(".mp4", ".wav")
        wav = wav.replace(".mkv", ".wav")
        wav = wav.replace(".webm", ".wav")

        if os.path.exists(wav) : 
            self.downloaded = True
            return wav
        return ""

    #it download the original file before, no need to do it manually
    def proxy(self, outputdir, onUpdate=None) : 
        if (self.findProxy(outputdir)) :
            if (onUpdate) : 
                onUpdate()
            return self.findProxy(outputdir)
        f = self.download(outputdir)
        self.infos = "Starting proxy conversion..."
        self.proxying = True
        if (onUpdate) : 
            onUpdate()
        converter = ffmpeg.Ffmpeg()
        self.infos = "Converting to proxy..."
        if (onUpdate) : 
            onUpdate()
        data = converter.proxy(f)
        if (onUpdate) : 
            onUpdate()
        self.infos = "Proxy created."
        self.proxying = False
        self.proxied = True
        return data

def search_query(searched) : 
    searched = searched.replace(" ", "+")
    process = subprocess.Popen(["curl", "https://www.youtube.com/results?search_query=" + searched], stdout=subprocess.PIPE)
    html = process.communicate()[0]
    html = html.decode("utf-8")
    data = html.split("ytInitialData")[1]
    while data[0] != "{" : 
        data = data[1:]

    while data[-2:] != "]}" : 
        data = data[:-1]

    try : 
        js = json.loads(data)
        return js
    except : 
        data = data.replace("{", "\n")
        data = data.replace("}", "\n")
        data = data.replace("[", "\n")
        data = data.replace("]", "\n")
        data = data.replace(",", "\n")
        data = data.replace("\"", "")
        lines = data.split("\n")
        ids = []
        added = []
        for i in range(len(lines)) : 
            l = lines[i]
            if "videoId" in l : 
                tmp = l.split(":")
                if (len(tmp[1]) == 11 and tmp[1] not in added) : 
                    added.append(tmp[1])
                    _id = {"id" : tmp[1], "title" : ""}
                    ids.append(_id)
                    k = i 
                    while k < len(lines) : 
                        if "text" in lines[k] : 
                            tmp2 = lines[k].split(":")
                            _id["title"] = tmp2[1]
                            break
                        k+= 1

        return ids

def videosFromQueryData(data) : 
    if type(data) == list : 
        videos = []
        for _id in data : 
            v = Video(_id["id"], _id["title"])
            videos.append(v)
        return videos
    contents = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
    videos = []

    print("Length of contents : " + str(len(contents)))

    for c in contents : 
        if "videoRenderer" not in c : 
            continue
        v = Video(c["videoRenderer"]["videoId"], 
                c["videoRenderer"]["title"]["runs"][0]["text"])
        videos.append(v)
    return videos

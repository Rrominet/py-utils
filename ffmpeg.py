import os 
import subprocess
import platform

class Ffmpeg : 
    def __init__(self, path="") : 
        self.path = path
        self.progress = {}

        if self.path == "" : 
            self.setGenericPath()

    def setGenericPath(self) : 
        if platform.system() == "Linux" or platform.system() == "Darwin" : 
            self.path = "ffmpeg"
        elif platform.system() == "Windows" : 
            self.path = "C:\\Program Files\\ffmpeg\\"
            if not os.path.isdir(os.path) : 
                self.path = "C:\\ffmpeg"
            if not os.path.isdir(os.path) : 
                self.path = "C:\\Program Files (x86)\\ffmpeg"

            if not os.path.isdir(os.path) : 
                self.path = "ffmpeg.exe"
                return

            self.path += os.sep + "bin\\ffmpeg.exe"

    #options is string like "-c:v libx264 -c:a aac"
    def convert(self, pin, out, options="") : 
        cmd = [self.path, "-i", pin]
        if len(options)>0 : 
            for o in options.split(" ") : 
                cmd.append(o)
        cmd.append("-progress")
        cmd.append("pipe:1")
        cmd.append("-y")
        cmd.append(out)

        with subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p : 
            for line in p.stdout : 
                tmp = line.split("=")
                if len(tmp)<2 : 
                    continue
                self.progress[tmp[0]] = tmp[1].replace("\n", "")

    def proxy(self, pin) : 
        out = ".".join(pin.split(".")[:-1]) + "_proxy.avi"
        self.convert(pin, out, "-c:v mjpeg")
        return out

    def wav(self, pin) : 
        out = ".".join(pin.split(".")[:-1]) + ".wav"
        self.convert(pin, out)
        return out

def convert(pin, out, options="") : 
    _ffmpeg = Ffmpeg()
    _ffmpeg.convert(pin, out, options)
    return _ffmpeg

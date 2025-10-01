from threading import Thread
import subprocess


class RunningProcess:
    def __init__(self, popen=None):
        self.popen = popen
        self.stdout = ""
        self.stderr = ""

    def out(self):
        if not self.popen:
            return ""
        out = self.popen.stdout.readline()
        if out:
            self.stdout += "\n" + out.strip()
        return self.stdout

    def err(self):
        if not self.popen:
            return ""
        out = self.popen.stderr.readline()
        if out:
            self.stdout += "\n" + out.strip()
        return self.stderr


def launchOnThread(args):
    res = RunningProcess()

    def func():
        res.popen = subprocess.Popen(args,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True)

    th = Thread(target=func)
    th.start()
    return res


def launch(args):
    return subprocess.run(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

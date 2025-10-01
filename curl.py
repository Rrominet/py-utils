import os
import subprocess
import json
curl = "/usr/bin/curl"

def headers_as_cmd(headers) : 
    r = []
    for h in headers : 
        r.append("-H")
        r.append(h + ": " + headers[h])
    return r

def formdata_as_cmd(formdata)  :
    r = []
    for f in formdata : 
        r.append("-F")
        r.append(f + "=" + formdata[f])
    return r

#formdata is a dir 
#if there are filepath in formdata, they need to have a @ prefix
def send_form(url, formdata, headers={}) : 
    cmd = [curl, "-X", "POST", url ] + headers_as_cmd(headers) + formdata_as_cmd(formdata)
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

#formdata is a dir 
#if there are filepath in formdata, they need to have a @ prefix
def send_json(url, json_data, headers={}) : 
    cmd = [curl, "-X", "POST", url ] + headers_as_cmd(headers) + ["-d", json.dumps(json_data)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout


def get(url, headers={}) :
    cmd = [curl, url] + headers_as_cmd(headers)
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

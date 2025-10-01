import sys 
v=sys.version_info.major
if v == 3 : 
    import urllib
    import urllib.request
    import ssl
else : 
    import urllib2
import json



def hasInternet() : 
    try :
        if v == 3 : 
            urllib.request.urlopen("http://google.com/", timeout=3)
        else : 
            urllib2.urlopen("http://google.com/", timeout=3)
        return True
    except : return False

def asJson(url, encoding = "utf-8") : 
    if v == 3 : 
        ctx = ssl._create_unverified_context()
        c = urllib.request.urlopen(url, context=ctx).read()
    else : 
        c = urllib2.urlopen(url).read()
    c = c.decode(encoding)
    return json.loads(c)

def download(dist, local) : 
    if v == 3 :
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(dist, context=ctx) as u : 
            f = open(local, 'wb')
            f.write(u.read())
            f.close()
    else : 
        from contextlib import closing 
        with closing(urllib2.urlopen(dist)) as u : 
            f = open(local, 'wb')
            f.write(u.read())
            f.close()

    return local

#data could be dict or string or any base python type
#only python3 for now
def send(url, data, format="utf-8") : 
    if type(data) != str : 
        data = urllib.parse.urlencode(data).encode(format)
    else :
        data = data.encode(format)
    ctx = ssl._create_unverified_context()
    r = urllib.request.Request(url, method="POST")
    try : 
        response = urllib.request.urlopen(r, data=data, context=ctx)
    except urllib.error.HTTPError as e : 
        print (e.reason)
        print (e.code)
        print (e.headers)
        return None
        
    if format == "raw"	 : 
        return response.read()
    return response.read().decode(format)

def get(url, params="", format="utf-8") :
    try : 
        res = urllib.request.urlopen(url + params)
        if format == "raw" : 
            return res.read()
        return res.read().decode(format)
    except urllib.error.HTTPError as e : 
        print (e.reason)
        print (e.code)
        print (e.headers)
        return None

def post(url, data={}, headers={}, format="utf-8", isJson=True) :
    """
    Sends a POST request with given data.

    :param url: URL to send the request to
    :param data: Data to send in the request body as JSON
    :param headers: Additional headers to include in the request
    :param format: Format to decode the response (default is utf-8), or "raw" to return as bytes
    :return: Decoded response or raw response bytes, or None on error
    """
    try:
        if isJson  :
            # Convert the dictionary to a JSON string
            data = json.dumps(data).encode(format)
            # Add content type header for JSON, and any additional headers
            headers['Content-Type'] = 'application/json'
        
        # Create the request
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        context = ssl._create_unverified_context()

        # Send the request
        with urllib.request.urlopen(req, context=context) as res:
            if format == "raw":
                return res.read()
            return res.read().decode(format)
    except urllib.error.HTTPError as e : 
        print (e.reason)
        print (e.code)
        print (e.headers)
        return None


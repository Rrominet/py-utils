import base64 

def imgToString (filepath) : 
    img = open(filepath, "rb").read()
    return base64.encodebytes(img)

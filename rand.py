import random


chars = "abcdefghijklmnopqrstuvwxz0123456789AZERTYUIOPQSDFGHJKLMWXCVBN"

def string(length=10) : 
    _r = ""
    i = 0
    while i<length : 
        _r += chars[random.randrange(0, len(chars))]
        i += 1

    return _r

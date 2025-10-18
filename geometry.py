import math

def translated(point, vector):
    return [point[0] + vector[0], point[1] + vector[1]]

def translatedPoints(points, vector):
    _r = []
    for p in points:
        p = translated(p, vector)
        _r.append(p)
    return _r


def rotated(point, angle, origin=(0,0)):
    x, y = point
    xo, yo = origin

    teta = math.atan(y/y)
    x2 = math.sqrt(pow(x - xo, 2) + pow(y - yo, 2)) * math.cos(angle + teta)
    y2 = math.sqrt(pow(x - xo, 2) + pow(y - yo, 2)) * math.sin(angle + teta)

    return (x2, y2)


def rotatedPoints(points, angle, origin=(0,0)):
    _r = []
    for p in points:
        p = rotated(p, angle, origin)
        _r.append(p)
    return _r

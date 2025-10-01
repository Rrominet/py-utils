from math import *
from mathutils import *

def dist (a, b) : 
    return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

def isInside(verticesCo, verticeCo, maxDistance) : 
    minX = 0 
    maxX = 0

    minY = 0
    maxY = 0

    minZ = 0
    maxZ = 0

    for v in verticesCo : 
        if v[0]<minX : 
            minX = v[0]

        if v[0]>maxX : 
            maxX = v[0]
        
        
        if v[1]<minY : 
            minY = v[1]

        if v[1]>maxY : 
            maxY = v[1]
        

        if v[2]<minZ : 
            minZ = v[2]

        if v[2]>maxZ : 
            maxZ = v[2]

    x = False 
    y = False 
    z = False

    if verticeCo[0]>= minX-maxDistance and verticeCo[0]<= maxX + maxDistance : 
        x = True

    if verticeCo[1]>= minY-maxDistance and verticeCo[1]<= maxY + maxDistance : 
        y = True

    if verticeCo[2]>= minZ-maxDistance and verticeCo[2]<= maxZ + maxDistance : 
        z = True

    if x and y and z : 
        return True 

    else : 
        return False

def center(bmVerts) : 
    x = 0.0
    y = 0.0
    z = 0.0

    xs = []
    ys = []
    zs = []

    i = 0
    while i<len(bmVerts) : 
        xs.append (bmVerts[i].co[0])
        ys.append (bmVerts[i].co[1])
        zs.append (bmVerts[i].co[2])

        i+=1


    x = sum(xs)/len(xs)
    y = sum(ys)/len(ys)
    z = sum(zs)/len(zs)

    return Vector ([x, y, z])








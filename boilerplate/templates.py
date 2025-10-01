import os
import shutil
from ml import fileTools as ft

#the name could be a fullpath if not it will find the name under ./templates_files/*
#dest is the destination of the created file/dir
def create(name, dest) : 
    src = name
    if not os.path.exists(src) : 
        src = os.path.dirname(__file__) + os.sep + "templates_files" + os.sep + name
        if not os.path.exists(src) : 
            print ("Error : could not find the template file : " + name)
            return

    if not os.path.isdir(src) : 
        shutil.copy(src, dest)
        print ("File " + dest + " created.")
    else : 
        shutil.copytree(src, dest)
        print ("Directory " + dest + " created.")

#test

#create("blender_addon", "/tmp/new-addon")


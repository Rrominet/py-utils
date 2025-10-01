import bpy

cls = []

def register() : 
    for c in cls : 
        bpy.utils.register_class(c)

def unregister() : 
    for c in cls : 
        bpy.utils.unregister_class(c)

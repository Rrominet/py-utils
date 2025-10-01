import bpy

class Prefs(bpy.types.AddonPreferences) : 
    bl_idname = __package__

    def draw(self, ctx) : 
        pass

cls = [Prefs]

def get() : 
    return bpy.context.preferences.addons[__package__].preferences

def register() : 
    for c in cls : 
        bpy.utils.register_class(c)

def unregister() : 
    for c in cls : 
        bpy.utils.unregister_class(c)

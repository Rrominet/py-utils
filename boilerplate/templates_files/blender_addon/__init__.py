bl_info = {
    "name": "",
    "author": "Romain Gilliot",
    "version": (1, 0),
    "blender" : (4, 2, 0),
    "location": "",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Le Plug Qui Facilite La Vie",
    }

import bpy

from . import ops
from . import props
from . import panels
from . import menus
from . import prefs

mdls = (ops, props, panels, menus, prefs, )

def register() : 
    for m in mdls : 
        m.register()

def unregister() : 
    for m in mdls : 
        m.unregister()

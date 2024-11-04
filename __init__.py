from .utils import register_modules, unregister_modules
from .modules import modules
from .keybindings import key_spaces
import bpy
 
bl_info = {
    "name": "Zenu",
    "author": "Zenker",
    "description": "",
    "blender": (4, 0, 0),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}


class ZenUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout


def register():
    for i in key_spaces:
        i.register()

    register_modules(modules)


def unregister():
    for i in key_spaces:
        i.unregister()

    unregister_modules(modules)

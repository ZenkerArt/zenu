from .modules import modules
import bpy

bl_info = {
    "name": "zenu",
    "author": "Zenker",
    "description": "",
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}


class ZenUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        # print(__name__)


def register():
    for i in modules:
        i.register()
    bpy.utils.register_class(ZenUtilsPreferences)


def unregister():
    for i in modules:
        i.unregister()
    bpy.utils.unregister_class(ZenUtilsPreferences)

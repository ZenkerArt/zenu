from .package_name import package_name
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
    bl_idname = package_name

    pie_menu: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout
        for mod in modules:
            panel = getattr(mod, 'addon_panel', None)

            if panel is not None:
                panel(self, layout)
        # context_pie_addon_panel(self, layout)


reg, unreg = bpy.utils.register_classes_factory((
    ZenUtilsPreferences,
))


def register():
    reg()
    for i in key_spaces:
        i.register()

    register_modules(modules)


def unregister():
    unreg()
    for i in key_spaces:
        i.unregister()

    unregister_modules(modules)

import bpy
from . import audio
from ... import register_modules, unregister_modules

reg, unreg = bpy.utils.register_classes_factory((

))

modules = (
    audio,
)

def register():
    reg()
    register_modules(modules)


def unregister():
    unreg()
    unregister_modules(modules)

import bpy
from bpy.app.handlers import persistent


def clamp(value: float, imim=0, imax=1):
    return min(max(value, imim), imax)


def clampi(x):
    return 1 - clamp(x)


@persistent
def load_handler(dummy):
    dns = bpy.app.driver_namespace
    dns["clamp"] = clamp
    dns["clampi"] = clampi


def register():
    load_handler(None)
    bpy.app.handlers.load_post.append(load_handler)


def unregister():
    bpy.app.handlers.load_post.remove(load_handler)

import bpy

reg, unreg = bpy.utils.register_classes_factory((
))


def register():
    reg()
    # print(draw_funcs)


def unregister():
    unreg()

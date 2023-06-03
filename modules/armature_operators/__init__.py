import bpy
from ...utils import is_type


class ZENU_OT_align_bone(bpy.types.Operator):
    bl_label = 'Align Bone'
    bl_idname = 'zenu.align_bone'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Armature) and context.active_bone

    def execute(self, context: bpy.types.Context):
        arm = context.active_object.data
        bone = context.active_bone
        bone.tail.x = bone.head.x
        bone.tail.y = bone.head.y
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_align_bone,
))


def register():
    reg()


def unregister():
    unreg()

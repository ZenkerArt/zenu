import bpy
from ....base_panel import BasePanel


class ZENU_OT_clear_bone_animation(bpy.types.Operator):
    bl_label = 'Clear Bone Animation'
    bl_idname = 'zenu.clear_bone_animation'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        actions = [strip.action for strip in context.selected_nla_strips]
        names = [i.name for i in context.selected_pose_bones]

        for action in actions:
            for curve in action.fcurves:
                try:
                    if curve.group.name in names:
                        action.fcurves.remove(curve)
                except Exception:
                    self.report({'WARNING'}, f'Skip curve')

        return {'FINISHED'}


class ZENU_PT_nla_clear_animation(BasePanel):
    bl_label = 'Clear Animation'
    bl_space_type = 'NLA_EDITOR'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_clear_bone_animation.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_clear_bone_animation,
    ZENU_PT_nla_clear_animation
))


def register():
    reg()


def unregister():
    unreg()

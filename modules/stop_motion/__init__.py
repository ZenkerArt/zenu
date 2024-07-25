import bpy
from ...base_panel import BasePanel


class ZENU_OT_sm_insert_frame(bpy.types.Operator):
    bl_label = 'Insert Frame'
    bl_idname = 'zenu.sm_insert_frame'

    def execute(self, context: bpy.types.Context):
        context.active_object.shape_key_add(name='frame')
        return {'FINISHED'}


class ZENU_PT_stop_motion(BasePanel):
    bl_label = 'Stop Motion'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_sm_insert_frame.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_sm_insert_frame,
    ZENU_PT_stop_motion,
))


def register():
    reg()


def unregister():
    unreg()

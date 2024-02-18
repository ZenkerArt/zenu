import bpy
from ...base_panel import BasePanel


class ZENU_OT_select_uv_shell(bpy.types.Operator):
    bl_label = 'Select UV Shell'
    bl_idname = 'zenu.select_uv_shell'

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}


class ZENU_PT_uv_utils(BasePanel):
    bl_label = 'UV Utils'
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_select_uv_shell.bl_idname)
        mesh: bpy.types.Mesh = context.active_object.data
        uv_layer = mesh.uv_layers.active

        print(uv_layer.uv)

        # layout.


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_uv_utils,
    ZENU_OT_select_uv_shell,
))


def register():
    reg()


def unregister():
    unreg()

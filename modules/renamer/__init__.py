import bpy
from ...base_panel import BasePanel


class ZENU_PT_Renamer(BasePanel):
    bl_label = 'Renamer'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

class ZENU_OT_name(bpy.types.Operator):
    bl_label = 'label'
    bl_idname = 'zenu.name'

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_Renamer,
))


def register():
    reg()


def unregister():
    unreg()

import bpy
from .create_project import ZENU_OT_create_project
from ...base_panel import BasePanel



class ZENU_PT_project_manager(BasePanel):
    bl_label = 'Project Manager'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_create_project.bl_idname)
        

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_project_manager,
    ZENU_OT_create_project
))

def register():
    reg()


def unregister():
    unreg()

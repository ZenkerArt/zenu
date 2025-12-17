import bpy
from bpy_extras.io_utils import ExportHelper



class ZENU_OT_create_project(bpy.types.Operator):
    bl_label = 'Create Project'
    bl_idname = 'zenu.create_project'

    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'}, default='')
    
    
    def execute(self, context: bpy.types.Context):
        print(self.filepath)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.filepath = 'Project name'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

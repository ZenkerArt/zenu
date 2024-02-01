import bpy
from ...utils import check_mods

active_mesh = None


class ZENU_OT_extract_mesh(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    bl_label = 'Extract'
    bl_idname = 'zenu.extract_mesh'
    curve_data: bpy.types.Curve
    start_mouse = 0

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return check_mods('e')

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        name = obj.name
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate()

        split = [i for i in context.selected_objects if i.name != name][0]

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        split.select_set(True)
        context.view_layer.objects.active = split
        bpy.ops.object.mode_set(mode='EDIT')

        global active_mesh
        active_mesh = split

        bpy.ops.mesh.select_all()
        # bpy.ops.transform.shrink_fatten()

        bpy.ops.transform.shrink_fatten('INVOKE_DEFAULT')

        return {'FINISHED'}

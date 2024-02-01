import bpy
from ...utils import check_mods

active_curve = None


class ZENU_OT_data_transfer(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    bl_label = 'Transfer Weight'
    bl_idname = 'zenu.transfer_weight'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        data = [isinstance(obj.data, bpy.types.Mesh) for obj in context.selected_objects]

        return check_mods('eo') and any(data) and len(data) > 1

    def execute(self, context: bpy.types.Context):
        active = context.active_object
        objects = [i for i in context.selected_objects if i != active]

        for obj in objects:
            mod: bpy.types.DataTransferModifier = obj.modifiers.new('ZENU_DATA_TRANSFER', 'DATA_TRANSFER')
            mod.use_vert_data = True
            mod.data_types_verts = {'VGROUP_WEIGHTS'}
            mod.object = active
            with bpy.context.temp_override(object=obj):
                bpy.ops.object.datalayout_transfer(modifier="ZENU_DATA_TRANSFER")
                bpy.ops.object.modifier_apply(modifier="ZENU_DATA_TRANSFER")

        return {'FINISHED'}

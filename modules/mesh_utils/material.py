import bpy
from ...utils import check_mods


def new_material(name: str, color: tuple[float, float, float, float] = (1, 1, 1, 1)):
    mat = bpy.data.materials.get(name)

    if mat is None:
        mat = bpy.data.materials.new(name=name)

    mat.use_nodes = True
    mat.diffuse_color = color
    for node in mat.node_tree.nodes:
        if node.name != 'Principled BSDF': continue

        node.inputs['Base Color'].default_value = color

    return mat


class ZENU_OT_assign_material_active_polygon(bpy.types.Operator):
    bl_options = {'UNDO'}
    bl_label = 'Assign Material'
    bl_idname = 'zenu.assign_material_active_polygon'
    name: bpy.props.StringProperty('Material Name')
    color: bpy.props.FloatVectorProperty('Color', subtype='COLOR')
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return check_mods('e')

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        name = self.name
        slot: bpy.types.MaterialSlot = obj.material_slots.get(name)

        if slot is not None and name == slot.name:
            obj.active_material_index = slot.slot_index
            bpy.ops.object.material_slot_assign()
            return {'FINISHED'}
        elif slot is not None:
            obj.active_material_index = slot.slot_index
            obj.active_material = new_material(name, color=(*self.color, 1))
            return {'FINISHED'}

        bpy.ops.object.material_slot_add()
        obj.active_material = new_material(name, color=(*self.color, 1))
        bpy.ops.object.material_slot_assign()

        return {'FINISHED'}

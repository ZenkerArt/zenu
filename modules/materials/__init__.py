import bpy
from ...base_panel import BasePanel


class ZENU_OT_duplicate_material_slots(bpy.types.Operator):
    bl_options = {'UNDO'}
    bl_label = 'Duplicate Material Slots'
    bl_idname = 'zenu.duplicate_material_slots'

    type_rename: bpy.props.EnumProperty(items=(
        ('POSTFIX', 'Postfix', ''),
        ('PREFIX', 'Prefix', ''),
        ('REPLACE', 'Replace', ''),
    ), name='Replace Name')

    value: bpy.props.StringProperty()

    def rename_material(self, name: str, value: str, type: str):
        if type == 'POSTFIX':
            return name + value

        if type == 'PREFIX':
            return value + name

        if type == 'Replace':
            return value

        return name

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        layout.prop(self, 'type_rename', text='')

        col = layout.row()

        # col.label(text='Text')
        col = layout.column(align=True)
        col.prop(self, 'value', text='Text')

    def execute(self, context: bpy.types.Context):
        value = self.value
        type_rename = self.type_rename

        for obj in context.selected_objects:
            for slot in obj.material_slots:
                mat = slot.material.copy()
                mat.name = self.rename_material(slot.material.name, value, type_rename)
                slot.material = mat
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ZENU_PT_materials(BasePanel):
    bl_label = 'Materials'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        ob = context.object
        layout.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=5)
        layout.operator(ZENU_OT_duplicate_material_slots.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_duplicate_material_slots,
    ZENU_PT_materials,
))


def register():
    reg()


def unregister():
    unreg()

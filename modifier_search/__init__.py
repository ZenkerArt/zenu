import bpy
from ..base_panel import BasePanel
from ..utils import get_modifier


def modifier_search():
    items = []
    for item in bpy.types.Modifier.bl_rna.properties['type'].enum_items:
        items.append((item.identifier, item.name, item.description, item.icon, item.value))
    return items


class ZENU_OT_modifier_switch_search(bpy.types.Operator):
    bl_label = 'Switch Search Modifier'
    bl_idname = 'zenu.modifier_switch_search'

    modifier: bpy.props.EnumProperty(items=modifier_search())

    def execute(self, context: bpy.types.Context):
        context.scene.modifier_search = self.modifier
        return {'FINISHED'}


class ZENU_UL_modifier_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')
        row = layout.row(align=True)
        cloth = get_modifier(item, bpy.types.SubsurfModifier)

        row.prop(cloth, 'show_render', text='')
        row.prop(cloth, 'show_viewport', text='')
        row.prop(item, 'hide_viewport', text='', icon='RADIOBUT_ON')

    def filter_items(self, context: bpy.types.Context, data: bpy.types.AnyType, property: str):
        items = getattr(data, property)
        filtered = [0] * len(items)
        for index, obj in enumerate(items):
            cloth = get_modifier(obj, context.scene.modifier_search)
            if cloth is None:
                continue

            filtered[index] = self.bitflag_filter_item
        ordered = []

        return filtered, ordered


class ZENU_PT_modifier(BasePanel):
    bl_label = 'Modifier Search'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row()
        row.scale_y = 1.5
        row.prop(context.scene, 'modifier_search', text='')

        col = layout.column_flow(align=True)
        m = col.operator(ZENU_OT_modifier_switch_search.bl_idname, text='Subsurface')
        m.modifier = 'SUBSURF'
        m = col.operator(ZENU_OT_modifier_switch_search.bl_idname, text='Solidify')
        m.modifier = 'SOLIDIFY'

        layout.template_list('ZENU_UL_modifier_groups', '',
                             bpy.data, 'objects',
                             context.scene, 'physic_group_active')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_modifier,
    ZENU_UL_modifier_groups,
    ZENU_OT_modifier_switch_search
))


def register():
    bpy.types.Scene.modifier_search = bpy.props.EnumProperty(items=modifier_search(), default='SUBSURF')
    reg()


def unregister():
    unreg()

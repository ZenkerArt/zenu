import bpy
import bpy.types
from .operators import ZENU_OT_physic_select_all, ZENU_OT_physic_save, ZENU_OT_physic_load
from .utils import get_cloth
from ...base_panel import BasePanel
from ...utils import check_mods, is_mesh


class ZENU_UL_physic_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')
        row = layout.row(align=True)
        cloth = get_cloth(item)
        row.prop(cloth, 'show_render', text='')
        row.prop(cloth, 'show_viewport', text='')
        row.prop(item, 'hide_viewport', text='', icon='RADIOBUT_ON')

    def filter_items(self, context: bpy.types.Context, data: bpy.types.AnyType, property: str):
        items = getattr(data, property)
        filtered = [0] * len(items)
        for index, obj in enumerate(items):
            cloth = get_cloth(obj)
            if cloth is None:
                continue

            filtered[index] = self.bitflag_filter_item
        ordered = []

        return filtered, ordered


class ZENU_PT_physic(BasePanel):
    bl_label = 'Physic'
    bl_context = ''

    @classmethod
    def poll(cls, context: 'Context'):
        return check_mods('opesw')

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        cloth = get_cloth(context.active_object)

        row = layout.row()
        row.scale_y = 1.5
        if not cloth and is_mesh(context.active_object):
            mod = row.operator('object.modifier_add', text='Add Physic')
            mod.type = 'CLOTH'

        row = layout.row()
        row.scale_y = 1.5

        row.operator(ZENU_OT_physic_select_all.bl_idname, icon='RESTRICT_SELECT_OFF')

        layout.template_list('ZENU_UL_physic_groups', '',
                             bpy.data, 'objects',
                             context.scene, 'physic_group_active')
        if cloth is not None:
            self.draw_settings(context)

    def draw_settings(self, context: bpy.types.Context):
        layout = self.layout
        cloth = get_cloth(context.active_object)
        cache = cloth.point_cache
        layout.label(text=context.active_object.name)

        sp = layout.split(align=True)
        sp.prop(cloth, 'show_viewport')
        sp.prop(cloth, 'show_render')


class ZENU_PT_physic_presets(BasePanel):
    bl_label = 'Presets'
    bl_parent_id = 'ZENU_PT_physic'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_cloth(context.active_object)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        cloth = get_cloth(context.active_object)
        cloth_settings = cloth.settings
        collision_settings = cloth.collision_settings
        obj = context.active_object

        col = layout.column_flow(align=True)
        row = col.row(align=True)
        row.prop(context.scene, 'physic_presets', text='')
        op = col.operator(ZENU_OT_physic_save.bl_idname)
        op.to_clipboard = False
        op = col.operator(ZENU_OT_physic_load.bl_idname)
        op.from_clipboard = False

        col = layout.column_flow(align=True)
        op = col.operator(ZENU_OT_physic_save.bl_idname, text='Save To Clipboard')
        op.to_clipboard = True
        op = col.operator(ZENU_OT_physic_load.bl_idname, text='Load From Clipboard')
        op.from_clipboard = True

        col = layout.column_flow(align=True)
        col.prop(cloth_settings, 'time_scale')
        col.prop(cloth_settings, 'mass')

        col = layout.column_flow(align=True)
        col.prop_search(cloth_settings, "vertex_group_mass", obj, "vertex_groups", icon='PINNED', text='')
        col.prop(cloth_settings, "pin_stiffness", text="Stiffness")

        col = layout.column_flow(align=True)
        col.prop(collision_settings, "use_collision", text='Collision', icon='RESTRICT_VIEW_OFF')
        col.prop(collision_settings, "distance_min", slider=True, text="Distance")

        col = layout.column_flow(align=True)
        col.prop(collision_settings, "use_self_collision", text='Self Collision', icon='RESTRICT_VIEW_OFF')
        col.prop(collision_settings, "self_distance_min", slider=True, text="Distance")
        # col.prop(cloth_settings, 'vertex_group_mass', text='')


classes = (
    ZENU_PT_physic,
    ZENU_PT_physic_presets,
    ZENU_UL_physic_groups
)

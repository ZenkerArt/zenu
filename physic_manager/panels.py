import bpy
import bpy.types
from ..base_panel import BasePanel
from .operators import ZENU_OT_physic_bake_object, ZENU_OT_physic_rest_time_object, \
    ZENU_OT_physic_rest_time_scene, ZENU_OT_physic_select_all, ZENU_OT_physic_save, ZENU_OT_physic_load, \
    ZENU_OT_physic_create_preset, ZENU_OT_physic_remove_preset
from .utils import get_cloth
from ..utils import check_mods, is_mesh


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

        col = layout.column_flow(align=True)
        col.enabled = True
        if cache.is_baked is True:
            col.operator(ZENU_OT_physic_bake_object.bl_idname, text="Delete Bake").type = 'free'
        else:
            col.operator(ZENU_OT_physic_bake_object.bl_idname, text="Bake").type = 'bake'

        col.operator(ZENU_OT_physic_bake_object.bl_idname, text="Calculate to Frame").type = 'frame'

        settings = context.active_object.physic_setting
        sp = layout.column_flow(align=True)
        grid = sp.grid_flow(columns=2, align=True)
        grid.prop(settings, 'start')
        grid.prop(settings, 'end')
        grid.operator(ZENU_OT_physic_rest_time_object.bl_idname, text='', icon='PANEL_CLOSE').end = False
        grid.operator(ZENU_OT_physic_rest_time_object.bl_idname, text='', icon='PANEL_CLOSE').end = True
        sp.prop(settings, 'ignore', icon='PANEL_CLOSE')
        sp = layout.split(align=True)
        sp.prop(cloth, 'show_viewport')
        sp.prop(cloth, 'show_render')
        layout.label(text=f'{cache.frame_start}:{cache.frame_end}')


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
        row.operator(ZENU_OT_physic_create_preset.bl_idname, text='', icon='ADD')
        row.operator(ZENU_OT_physic_remove_preset.bl_idname, text='', icon='REMOVE')
        col.operator(ZENU_OT_physic_save.bl_idname)
        col.operator(ZENU_OT_physic_load.bl_idname)

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




class ZENU_PT_physic_bake_global(BasePanel):
    bl_label = 'Bake Global'
    bl_parent_id = 'ZENU_PT_physic'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column_flow(align=True)
        col.operator("ptcache.bake_all", text="Bake All Dynamics").bake = True
        col.operator("ptcache.free_bake_all", text="Delete All Bakes")
        col.operator("ptcache.bake_all", text="Update All to Frame").bake = False

        settings = context.scene.physic_setting
        sp = layout.grid_flow(align=True, columns=2)
        sp.prop(settings, 'start')
        sp.prop(settings, 'end')
        sp.operator(ZENU_OT_physic_rest_time_scene.bl_idname, text='', icon='PANEL_CLOSE').end = False
        sp.operator(ZENU_OT_physic_rest_time_scene.bl_idname, text='', icon='PANEL_CLOSE').end = True


classes = (
    ZENU_PT_physic,
    ZENU_PT_physic_presets,
    ZENU_PT_physic_bake_global,
    ZENU_UL_physic_groups
)

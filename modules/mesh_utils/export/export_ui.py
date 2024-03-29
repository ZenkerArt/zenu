import bpy
from .export_settings import ExportPointSettings, ZENU_OT_add_export_settings, ZENU_OT_remove_export_settings
from ...menu_manager import menu_3d_view, OperatorItem
from ....base_panel import BasePanel
from .export_points import ZENU_OT_remove_export_point, ZENU_OT_add_export_point, \
    ZENU_OT_assign_export_point, ZENU_OT_select_export_point, ZENU_OT_export_point
from .export_utils import ZENU_OT_export_by_name, ZENU_OT_export_by_collection


class ZENU_UL_export_points(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False)


class ZENU_UL_export_points_settings(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False)


class ZENU_PT_assign_panel(bpy.types.Panel):
    bl_idname = 'ZENU_PT_assign_panel'
    bl_label = 'Assign Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "object"

    # @classmethod
    # def poll(cls, context: bpy.types.Context):
    #     return True

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.template_list('ZENU_UL_export_points', '',
                          context.scene, 'zenu_export_points',
                          context.scene, 'zenu_export_points_index')
        try:
            point = context.scene.zenu_export_points[context.scene.zenu_export_points_index]
            row = layout.row(align=True)
            op = row.operator(ZENU_OT_assign_export_point.bl_idname, text='Assign')
            op.action = 'ASSIGN'
            op = row.operator(ZENU_OT_assign_export_point.bl_idname, text='Remove')
            op.action = 'REMOVE'
            row.operator(ZENU_OT_select_export_point.bl_idname, text='Select')

            # layout.prop(obj, 'zenu_export_point')
        except IndexError:
            pass


class ZENU_PT_export_utils(BasePanel):
    bl_label = 'Export Utils'
    bl_parent_id = 'ZENU_PT_export'

    def draw(self, context: bpy.types.Context):
        layout = self.layout.column(align=True)
        layout.operator(ZENU_OT_export_by_name.bl_idname)
        layout.operator(ZENU_OT_export_by_collection.bl_idname)


class ZENU_PT_export_points(BasePanel):
    bl_label = 'Export Points'
    bl_parent_id = 'ZENU_PT_export'

    def fbx_layout(self):
        settings = ExportPointSettings.get_active()
        layout = self.layout

        def prop(prop_name: str):
            icon = 'RADIOBUT_OFF'

            if getattr(settings, prop_name):
                icon = 'RADIOBUT_ON'

            box.prop(settings, prop_name, icon=icon)

        box = layout.box().column(align=True)
        prop('fbx_apply_modifiers')
        prop('fbx_apply_transforms')

        box = layout.box().column(align=True)
        prop('fbx_use_leaf_bones')
        prop('fbx_only_deform_bones')

        box = layout.box().column(align=True)
        prop('fbx_bake_animation')
        prop('fbx_only_deform_bones')
        prop('fbx_key_all_bones')
        prop('fbx_nla_strips')
        prop('fbx_all_actions')
        prop('fbx_force_start_end_keying')

    def export_settings(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        row = layout.row(align=True)
        row.template_list('ZENU_UL_export_points_settings', '',
                          context.scene, 'zenu_export_points_settings',
                          context.scene, 'zenu_export_points_settings_index')

        col = row.column(align=True)
        col.operator(ZENU_OT_add_export_settings.bl_idname, icon='ADD', text='')
        col.operator(ZENU_OT_remove_export_settings.bl_idname, icon='REMOVE', text='')

        self.fbx_layout()

    def export_assign(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object
        row = layout.row(align=True)

        row.template_list('ZENU_UL_export_points', '',
                          context.scene, 'zenu_export_points',
                          context.scene, 'zenu_export_points_index')

        row = row.column(align=True)
        row.operator(ZENU_OT_add_export_point.bl_idname, icon='ADD', text='')
        row.operator(ZENU_OT_remove_export_point.bl_idname, icon='REMOVE', text='')

        try:
            point = context.scene.zenu_export_points[context.scene.zenu_export_points_index]
            row = layout.row(align=True)
            op = row.operator(ZENU_OT_assign_export_point.bl_idname, text='Assign')
            op.action = 'ASSIGN'
            op = row.operator(ZENU_OT_assign_export_point.bl_idname, text='Remove')
            op.action = 'REMOVE'
            row.operator(ZENU_OT_select_export_point.bl_idname, text='Select')
            op = layout.operator(ZENU_OT_export_point.bl_idname, text='Export')
            op.export_active = False

            col = layout.column(align=True)
            col.prop(point, 'path', text='')
            col.prop(point, 'name', text='')
            col.prop(point, 'settings', text='')

            # layout.prop(obj, 'zenu_export_point')
        except IndexError:
            pass

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        tab = context.scene.zenu_export_point_tabs
        layout.prop(context.scene, 'zenu_export_point_tabs', expand=True)

        if tab == 'EXPORT_SETTINGS':
            self.export_settings(context, layout)
        elif tab == 'FILES':
            self.export_assign(context, layout)


class ZENU_PT_export(BasePanel):
    bl_label = 'Export'

    def draw(self, context: bpy.types.Context):
        layout = self.layout


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_export,
    ZENU_PT_export_utils,
    ZENU_PT_export_points,
    ZENU_PT_assign_panel,
    ZENU_UL_export_points,
    ZENU_UL_export_points_settings
))


def register():
    reg()

    bpy.types.Scene.zenu_export_point_tabs = bpy.props.EnumProperty(items=(
        ('FILES', 'Files', ''),
        ('EXPORT_SETTINGS', 'Export Settings', ''),
    ))

    menu_3d_view.right.add(OperatorItem(
        op='wm.call_panel',
        text='Export Panel',
        vars={'name': ZENU_PT_assign_panel.bl_idname}
    ))


def unregister():
    unreg()

import bpy
from ....base_panel import BasePanel
from .export_points import ZENU_OT_remove_export_point, ZENU_OT_add_export_point
from .export_utils import ZENU_OT_export_by_name, ZENU_OT_export_by_collection


class ZENU_UL_export_points(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name)


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

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        row = layout.row(align=True)

        row.template_list('ZENU_UL_export_points', '',
                          context.scene, 'zenu_export_points',
                          context.scene, 'zenu_export_points_index')

        col = row.column(align=True)
        col.operator(ZENU_OT_add_export_point.bl_idname, icon='ADD', text='')
        col.operator(ZENU_OT_remove_export_point.bl_idname, icon='REMOVE', text='')

        try:
            point = context.scene.zenu_export_points[context.scene.zenu_export_points_index]
            layout.prop(point, 'name', text='')
            layout.prop(point, 'path', text='')
            layout.prop(point, 'file_type', text='')
        except IndexError:
            pass


class ZENU_PT_export(BasePanel):
    bl_label = 'Export'

    def draw(self, context: bpy.types.Context):
        layout = self.layout


classes = (
    ZENU_PT_export,
    ZENU_PT_export_utils,
    ZENU_PT_export_points,
    ZENU_UL_export_points
)

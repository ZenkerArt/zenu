import bpy
from ...keybindings import view_3d
from ...utils import get_modifier
from ..utils_panel import ZENU_OT_change_display_type
from . import menus


class ZENU_MT_context(bpy.types.Menu):
    bl_label = 'Zenu Context'
    bl_idname = 'ZENU_MT_context'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        pie = layout.menu_pie()

        for menu in menus.classes:
            layout = pie.row()
            layout.scale_x = 1.5
            layout.scale_y = 1.5
            layout = layout.column(align=True)
            menu.draw(context, layout)

        # pie.separator()
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column(align=True)
        other_menu.scale_y = 1.5

        for menu in menus.classes:
            menu.draw_submenu(context, other_menu)

    def show_mods(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        mods = {
            'Subdiv': bpy.types.SubsurfModifier,
            'Cloth': bpy.types.ClothModifier,
            'Solidify': bpy.types.SolidifyModifier
        }
        row = layout.row()
        row.scale_x = 1.5
        row.scale_y = 1.5
        layout = row.column(align=True)

        for key, value in mods.items():
            mod = get_modifier(context.active_object, value)
            if mod:
                layout.prop(mod, 'show_viewport', text=key)

    def overlays(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object
        layout = layout.row()
        layout.scale_x = 1.5
        layout.scale_y = 1.5

        layout = layout.column(align=True)
        layout.prop(context.space_data.overlay, 'show_face_orientation')
        layout.prop(obj, 'show_wire')

        if obj.mode == 'EDIT':
            layout.prop(context.space_data.overlay, 'show_weight', text='Weights')

    def properties(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object

        layout = layout.row()
        layout.scale_x = 1.5
        layout.scale_y = 1.5
        layout = layout.column(align=True)

        layout.prop(obj, 'show_in_front')

        self.object_property(context, layout)

    def armature_property(self):
        pass

    def object_property(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object
        if obj.mode == 'OBJECT' and isinstance(obj.data, bpy.types.Mesh):
            row = layout.row(align=True)
            row.scale_x = .5
            row.operator('object.shade_smooth', text='Smooth')
            row.operator('object.shade_flat', text='Flat')
            row.prop(obj.data, 'use_auto_smooth', text='Auto')

        if not isinstance(obj.data, bpy.types.Armature):
            row = layout.row(align=True)
            ZENU_OT_change_display_type.button(row, 'WIRE')
            ZENU_OT_change_display_type.button(row, 'TEXTURED')

    def active_object(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        # self.show_mods(context, layout)
        # self.overlays(context, layout)
        # self.properties(context, layout)
        pass


class ZENU_OT_open_context_pie(bpy.types.Operator):
    bl_label = 'Context Pie'
    bl_idname = 'zenu.open_context_pie'

    def execute(self, context: bpy.types.Context):
        bpy.ops.wm.call_menu_pie(name=ZENU_MT_context.bl_idname)
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_open_context_pie,
    ZENU_MT_context
))


def register():
    view_3d.new(ZENU_OT_open_context_pie.bl_idname, type='W')
    reg()


def unregister():
    unreg()

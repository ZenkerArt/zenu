import bpy
from .enums import Modes
from .filters import any_object, only_armature, only_mesh, only_armature_weight, only_edit_mesh
from .operator_view import OperatorView
from .property_view import PropertyView
from ..menu_manager import menu_manager
from ..mesh_utils import ZENU_OT_edger, ZENU_OT_extract_mesh, ZENU_OT_data_transfer
from ..shape_key_bind import ZENU_OT_open_bind_shape_key
from ...keybindings import view_3d


def create_layout(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    actions_layout = layout.column(align=True)
    actions_layout.scale_x = 1.5
    actions_layout.scale_y = 1.5
    return actions_layout


class ZENU_MT_context(bpy.types.Menu):
    bl_label = 'Zenu Context'
    bl_idname = 'ZENU_MT_context'

    def draw(self, context: bpy.types.Context):
        obj = context.active_object
        obj_data = None
        if obj:
            obj_data = obj.data

        properties: list[PropertyView] = [
            [
                PropertyView(context.space_data.overlay, 'show_retopology', only_edit_mesh, active_object=obj),
                PropertyView(context.space_data.overlay, 'show_weight', only_edit_mesh, active_object=obj),
            ],
            [
                PropertyView(obj, 'show_in_front', any_object),
                PropertyView(obj_data, 'show_axes', only_armature, text="Axes"),
                PropertyView(obj_data, 'show_names', only_armature, text="Names"),
                PropertyView(obj, 'show_wire', only_mesh, text="Wireframe"),
            ],
            PropertyView(context.space_data.overlay, 'show_face_orientation', only_mesh, active_object=obj),
            PropertyView(context.scene.render, 'use_simplify', any_object)
        ]

        modifiers: list[OperatorView] = [
        ]

        actions: list[OperatorView] = [
            OperatorView(obj, 'object.convert', text='Convert To Mesh', vars={'target': 'MESH'}),
        ]

        actions_sub_panel = [
            PropertyView(obj_data, "display_type", only_armature, expand=True),
            PropertyView(obj, "display_type", only_mesh, expand=True),
            PropertyView(obj_data, "pose_position", only_armature, expand=True, use_row=True),
        ]

        layout = self.layout
        pie = layout.menu_pie()
        modifiers_layout = create_layout(pie)
        actions_layout = create_layout(pie)
        properties_layout = create_layout(pie)

        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column(align=True)
        other_menu.scale_y = 1.5
        propertiess_layout = other_menu

        def draw_panel(arr, lay):
            for i in arr:
                if isinstance(i, list):
                    l = lay.row(align=True)
                    l.scale_x = .8
                    draw_panel(i, l)
                    continue

                i.layout = lay
                i.draw()

        for i in menu_manager.right.all:
            i.draw(actions_layout, obj)

        for i in menu_manager.left.all:
            i.draw(modifiers_layout, obj)

        for i in menu_manager.down.all:
            i.draw(properties_layout, obj)

        draw_panel(modifiers, modifiers_layout)
        draw_panel(actions, actions_layout)
        draw_panel(properties, properties_layout)
        draw_panel(actions_sub_panel, propertiess_layout)


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
    view_3d.deactivate('W')
    unreg()

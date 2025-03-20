from dataclasses import dataclass

import bpy
from .enums import Modes
from .filters import any_object, only_armature, only_mesh, only_armature_weight, only_edit_mesh
from .operator_view import OperatorView
from .property_view import PropertyView
from ..menu_manager import menu_3d_view, MenuManager, menu_timeline
from ...keybindings import view_3d, dopesheet, graph_editor, sequence_editor


@dataclass
class PieMenuContext:
    mouse_region_x: int
    mouse_region_y: int


pie_menu_context = PieMenuContext(
    mouse_region_x=0,
    mouse_region_y=0
)


class ZENU_OT_change_keying_set(bpy.types.Operator):
    bl_label = 'Change Keying Set'
    bl_idname = 'zenu.change_keying_set'
    keying_set_name: bpy.props.StringProperty(name='Keying Set Name', default='Location & Rotation')

    def execute(self, context: bpy.types.Context):
        context.scene.keying_sets_all.active = dict(bpy.context.scene.keying_sets_all.items())[self.keying_set_name]
        return {'FINISHED'}

    @staticmethod
    def depress(name: str):
        if bpy.context.scene.keying_sets_all.active is None:
            return False

        val = bpy.context.scene.keying_sets_all.active.bl_label
        return val == name


def create_layout(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    actions_layout = layout.column(align=True)
    actions_layout.scale_x = 1.5
    actions_layout.scale_y = 1.5
    return actions_layout


@dataclass
class MenuContext:
    right_layout: bpy.types.UILayout
    left_layout: bpy.types.UILayout
    up_layout: bpy.types.UILayout
    down_layout: bpy.types.UILayout
    obj: bpy.types.Object


class ZENU_MT_context(bpy.types.Menu):
    bl_label = 'Zenu Context'
    bl_idname = 'ZENU_MT_context'

    def draw_menu(self, menu: MenuManager, context: MenuContext):
        obj = context.obj

        for i in menu.right.all:
            i.draw(context.right_layout, obj)

        for i in menu.left.all:
            i.draw(context.left_layout, obj)

        for i in menu.up.all:
            i.draw(context.up_layout, obj)

        for i in menu.down.all:
            i.draw(context.down_layout, obj)

    def draw_3d_view(self, context: bpy.types.Context, menu_context: MenuContext):
        obj = context.active_object
        obj_data = None
        if obj:
            obj_data = obj.data
        # bpy.context.object.pose.use_mirror_x = True

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
            PropertyView(bpy.context.object.pose, 'use_mirror_x', any_object, text="X Mirror"),
            PropertyView(context.space_data.overlay, 'show_face_orientation', only_mesh, active_object=obj),
            PropertyView(context.scene.render, 'use_simplify', any_object),
        ]
        # bpy.data.scenes["Scene"].sync_mode
        modifiers: list[OperatorView] = [
        ]

        actions: list[OperatorView] = [
            OperatorView(obj, ZENU_OT_change_keying_set.bl_idname, text='LocRot',
                         vars={'keying_set_name': 'Location & Rotation'},
                         depress=ZENU_OT_change_keying_set.depress('Location & Rotation')),
            OperatorView(obj, ZENU_OT_change_keying_set.bl_idname, text='LocRotScale',
                         vars={'keying_set_name': 'Location, Rotation & Scale'},
                         depress=ZENU_OT_change_keying_set.depress('Location, Rotation & Scale')),
            OperatorView(obj, ZENU_OT_change_keying_set.bl_idname, text='Whole Character',
                         vars={'keying_set_name': 'Whole Character'},
                         depress=ZENU_OT_change_keying_set.depress('Whole Character')),
        ]

        actions_sub_panel = [
            PropertyView(obj_data, "display_type", only_armature, expand=True),
            PropertyView(obj, "display_type", only_mesh, expand=True),
            PropertyView(obj_data, "pose_position", only_armature, expand=True, use_row=True),
            PropertyView(context.scene, 'sync_mode', any_object, expand=True, use_row=True)
        ]

        self.draw_menu(menu_3d_view, menu_context)
        self.draw_panel(modifiers, menu_context.left_layout)
        self.draw_panel(actions, menu_context.right_layout)
        self.draw_panel(properties, menu_context.down_layout)
        self.draw_panel(actions_sub_panel, menu_context.up_layout)

    def draw_panel(self, arr, lay):
        for i in arr:
            if isinstance(i, list):
                l = lay.row(align=True)
                l.scale_x = .8
                self.draw_panel(i, l)
                continue

            i.layout = lay
            i.draw()

    def draw(self, context: bpy.types.Context):
        obj = context.active_object
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

        menu_context = MenuContext(
            right_layout=actions_layout,
            left_layout=modifiers_layout,
            up_layout=other_menu,
            down_layout=properties_layout,
            obj=obj
        )

        if context.space_data.type == 'VIEW_3D':
            self.draw_3d_view(context, menu_context)
        elif context.space_data.type in {'DOPESHEET_EDITOR', 'GRAPH_EDITOR'}:
            self.draw_menu(menu_timeline, menu_context)


class ZENU_OT_open_context_pie(bpy.types.Operator):
    bl_label = 'Context Pie'
    bl_idname = 'zenu.open_context_pie'

    def execute(self, context: bpy.types.Context):
        bpy.ops.wm.call_menu_pie(name=ZENU_MT_context.bl_idname)
        return {'FINISHED'}

    def invoke(self, context, event):
        pie_menu_context.mouse_region_x = event.mouse_region_x
        pie_menu_context.mouse_region_y = event.mouse_region_y
        return self.execute(context)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_change_keying_set,
    ZENU_OT_open_context_pie,
    ZENU_MT_context
))


def register():
    reg()
    view_3d.new(ZENU_OT_open_context_pie.bl_idname, type='W')
    dopesheet.new(ZENU_OT_open_context_pie.bl_idname, type='W')
    graph_editor.new(ZENU_OT_open_context_pie.bl_idname, type='W')
    sequence_editor.new(ZENU_OT_open_context_pie.bl_idname, type='W')


def unregister():
    unreg()

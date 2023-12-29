from abc import ABC, abstractmethod
from typing import Callable, Any

import bpy
from .filters import any_object, only_armature, only_mesh, only_armature_weight
from .property_view import PropertyView
from ..armature_operators.selection import ZENU_OT_select_parent_objects, ZENU_OT_select_bones
from ..physic import ZENU_OT_bind_physic_to_active
from ..shape_key_bind import ZENU_OT_open_bind_shape_key
from ...keybindings import view_3d
from .enums import Modes


class OperatorView:
    _func: Callable[[bpy.types.Object], bool]
    _name: str
    _ops: str
    _obj: bpy.types.Object
    _vars: dict[str, Any] = {}
    layout: bpy.types.UILayout

    def __init__(self,
                 obj: bpy.types.Object, ops: str,
                 func: Callable[[bpy.types.Object], bool],
                 text: str = '',
                 vars: dict[str, Any] = None,
                 ):

        self._vars = vars

        if vars is None:
            self._vars = dict()

        self._func = func
        self._ops = ops
        self._obj = obj
        self._name = text

    def set_name(self, name: str):
        self._name = name

    def draw(self):
        layout = self.layout
        if not self._obj:
            return

        if not self._func(self._obj):
            return

        typed, operator = self._ops.split('.')

        if not getattr(getattr(bpy.ops, typed), operator).poll():
            return

        if self._name:
            op = layout.operator(self._ops, text=self._name)
        else:
            op = layout.operator(self._ops)

        for key, value in self._vars.items():
            setattr(op, key, value)


class ZENU_MT_context_test(bpy.types.Menu):
    bl_label = 'Zenu Context'
    bl_idname = 'ZENU_MT_context_test'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.template_node_operator_asset_root_items()
        # layout.operator()

class ZENU_MT_context(bpy.types.Menu):
    bl_label = 'Zenu Context'
    bl_idname = 'ZENU_MT_context'

    def create_layout(self, layout: bpy.types.UILayout) -> bpy.types.UILayout:
        actions_layout = layout.column(align=True)
        actions_layout.scale_x = 1.5
        actions_layout.scale_y = 1.5
        return actions_layout

    def draw(self, context: bpy.types.Context):
        obj = context.active_object
        obj_data = None
        if obj:
            obj_data = obj.data

        properties: list[PropertyView] = [

            PropertyView(context.space_data.overlay, "show_face_orientation", only_mesh, active_object=obj),
            [
                PropertyView(obj, "show_in_front", any_object),
                PropertyView(obj_data, "show_axes", only_armature, text="Axes"),
                PropertyView(obj_data, "show_names", only_armature, text="Names"),
                PropertyView(obj, "show_wire", only_mesh, text="Wireframe"),
            ]
        ]

        modifiers: list[OperatorView] = [
            OperatorView(obj, 'object.automirror', any_object),
            OperatorView(obj, 'object.modifier_add', only_mesh, vars={'type': 'MIRROR'}, text='Mirror'),
        ]

        actions: list[OperatorView] = [
            OperatorView(obj, 'object.convert', only_mesh, text='Convert To Mesh', vars={'target': 'MESH'}),
            OperatorView(obj, ZENU_OT_select_parent_objects.bl_idname, only_armature),
            OperatorView(obj, ZENU_OT_open_bind_shape_key.bl_idname, only_armature),
            OperatorView(obj, ZENU_OT_bind_physic_to_active.bl_idname, only_armature),
            OperatorView(obj, ZENU_OT_select_bones.bl_idname, only_mesh),
            OperatorView(obj, 'object.parent_set', only_armature_weight, vars={'type': 'ARMATURE_AUTO'},
                         text='Auto Weight'),
            OperatorView(obj, 'object.parent_set', only_armature_weight, vars={'type': 'ARMATURE'},
                         text='Without Weight'),
        ]

        actions_sub_panel = [
            OperatorView(obj, 'render.opengl', any_object, vars={'animation': True},
                         text='Render Preview Animation'),
            OperatorView(obj, 'nla.bake', any_object),
            PropertyView(obj_data, "display_type", only_armature, expand=True),
            PropertyView(obj, "display_type", only_mesh, expand=True),
            PropertyView(obj_data, "pose_position", only_armature, expand=True, use_row=True),

        ]

        layout = self.layout
        pie = layout.menu_pie()
        modifiers_layout = self.create_layout(pie)
        actions_layout = self.create_layout(pie)
        properties_layout = self.create_layout(pie)

        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column(align=True)
        other_menu.scale_y = 1.5
        propertiess_layout = other_menu


        actions_layout.template_node_operator_asset_root_items()

        def draw_panel(arr, lay):
            for i in arr:
                if isinstance(i, list):
                    l = lay.row(align=True)
                    draw_panel(i, l)
                    continue

                i.layout = lay
                i.draw()

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
    ZENU_MT_context_test,
    ZENU_OT_open_context_pie,
    ZENU_MT_context
))


def register():
    view_3d.new(ZENU_OT_open_context_pie.bl_idname, type='W')
    reg()


def unregister():
    unreg()

from abc import ABC, abstractmethod
from typing import Callable, Any

import bpy
from ..armature_operators.selection import ZENU_OT_select_parent_objects, ZENU_OT_select_bones
from ...keybindings import view_3d
from ...utils import is_type, check_mods


class Modes:
    OBJECT: str = 'OBJECT'
    EDIT: str = 'EDIT'
    POSE: str = 'POSE'
    SCULPT: str = 'SCULPT'
    VERTEX_PAINT: str = 'VERTEX_PAINT'
    WEIGHT_PAINT: str = 'WEIGHT_PAINT'
    TEXTURE_PAINT: str = 'TEXTURE_PAINT'
    PARTICLE_EDIT: str = 'PARTICLE_EDIT'
    EDIT_GPENCIL: str = 'EDIT_GPENCIL'


def only_armature(obj: bpy.types.Object) -> bool:
    return is_type(obj, bpy.types.Armature)


def only_armature_weight(obj: bpy.types.Object) -> bool:
    if len(bpy.context.selected_objects) <= 1:
        return False

    return is_type(obj, bpy.types.Armature) and check_mods('o')


def only_mesh(obj: bpy.types.Object) -> bool:
    return is_type(obj, bpy.types.Mesh)


def any_object(obj: bpy.types.Object) -> bool:
    return True


class PropertyView:
    _func: Callable[[bpy.types.Object], bool]
    _name: str
    _property: str
    _obj: bpy.types.Object
    _valid_object: bpy.types.Object
    _expand: bool = False
    _use_row: bool = False
    layout: bpy.types.UILayout

    def __init__(self,
                 obj: bpy.types.Object,
                 property: str,
                 func: Callable[[bpy.types.Object], bool],
                 text: str = '',
                 active_object: bpy.types.Object = None,
                 expand: bool = False,
                 use_row: bool = False
                 ):
        self._use_row = use_row
        self._func = func
        self._property = property
        self._name = text

        self._obj = obj
        self._valid_object = obj
        self._expand = expand
        if active_object:
            self._valid_object = active_object

    def set_name(self, name: str):
        self._name = name

    def draw(self):
        layout = self.layout
        if not self._obj or not self._valid_object:
            return

        if not self._func(self._valid_object):
            return

        if self._use_row:
            layout = layout.row()

        if self._name:
            layout.row(align=True).prop(self._obj, self._property, text=self._name, expand=self._expand)
        else:
            layout.row(align=True).prop(self._obj, self._property, expand=self._expand)


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
            PropertyView(obj, "show_in_front", any_object),
            PropertyView(obj_data, "show_axes", only_armature, text="Axes"),
            PropertyView(obj_data, "show_names", only_armature, text="Names"),
            PropertyView(obj, "show_wire", only_mesh, text="Wireframe"),
            PropertyView(context.space_data.overlay, "show_face_orientation", only_mesh, active_object=obj),
            PropertyView(obj_data, "pose_position", only_armature, expand=True, use_row=True),
        ]
        # bpy.ops.object.parent_set(type='ARMATURE')

        modifiers: list[OperatorView] = [
            OperatorView(obj, 'object.automirror', any_object),
        ]

        actions: list[OperatorView] = [
            OperatorView(obj, 'object.convert', only_mesh, text='Convert To Mesh', vars={'target': 'MESH'}),
            OperatorView(obj, ZENU_OT_select_parent_objects.bl_idname, only_armature),
            OperatorView(obj, ZENU_OT_select_bones.bl_idname, only_mesh),
            OperatorView(obj, 'object.parent_set', only_armature_weight, vars={'type': 'ARMATURE_AUTO'},
                         text='Auto Weight'),
            OperatorView(obj, 'object.parent_set', only_armature_weight, vars={'type': 'ARMATURE'},
                         text='Without Weight'),
        ]

        actionso = [
            OperatorView(obj, 'render.opengl', any_object, vars={'animation': True},
                         text='Render Preview Animation'),
        ]

        layout = self.layout
        pie = layout.menu_pie()
        modifiers_layout = self.create_layout(pie)
        actions_layout = self.create_layout(pie)
        properties_layout = self.create_layout(pie)
        propertiess_layout = self.create_layout(pie)

        for item in modifiers:
            item.layout = modifiers_layout
            item.draw()

        for item in actions:
            item.layout = actions_layout
            item.draw()

        for item in properties:
            item.layout = properties_layout
            item.draw()

        for item in actionso:
            item.layout = propertiess_layout
            item.draw()


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

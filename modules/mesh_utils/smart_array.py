import math

import bpy
from mathutils import Vector
from .drawer import Drawer
from ...utils import is_type


class ZENU_OT_array(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO_GROUPED', 'GRAB_CURSOR', 'BLOCKING'}
    bl_label = 'Array'
    bl_idname = 'zenu.array'
    _mouse_start_pos = (0, 0)
    _mouse_pos = (0, 0)
    _init_loc_x = 0
    _mod: bpy.types.ArrayModifier = None
    _count: int = 0
    _dir: int = 0
    _empty: bpy.types.Object = None
    _is_circle: bool = False

    _shift: bool = False
    _ctrl: bool = False
    drawer: Drawer

    def __init__(self):
        self.drawer = Drawer()

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Mesh)

    def init(self, obj: bpy.types.Object):
        self._count = 2
        self._mod = obj.modifiers.new(name='ZENU_Array', type='ARRAY')

    def circle(self, context: bpy.types.Context, offset: float):
        mod = self._mod
        mod.offset_object = self._empty
        vec = Vector((0, 0, 0))
        d = self._dir
        dd = self._dir
        ang = abs((math.pi * 2) / self._count)
        if self._dir == 0:
            d = 1
        elif self._dir == 1:
            d = 0
            ang = -ang
        elif self._dir == 2:
            dd = 0
            d = 2

        vec[dd] = offset
        self._empty.location = context.active_object.matrix_local @ vec
        self._empty.rotation_euler = context.active_object.rotation_euler
        self._empty.rotation_euler[d] += ang

    def line(self, context: bpy.types.Context, offset: float):
        mod = self._mod
        mod.relative_offset_displace = Vector((0, 0, 0))
        mod.relative_offset_displace[self._dir] = offset

    def create_empty(self):
        if self._is_circle and not self._empty:
            self._empty = bpy.data.objects.new('ZENU_RadialArray', None)
            bpy.context.scene.collection.objects.link(self._empty)
        elif self._empty is not None:
            bpy.data.objects.remove(self._empty)
            self._empty = None

    def execute(self, context):
        if self._mod is None:
            return

        mod = self._mod
        mod.use_relative_offset = not self._is_circle
        mod.use_object_offset = self._is_circle

        value = self._mouse_pos[0] - self._mouse_start_pos[0]
        mod.count = self._count

        result = value / 100

        if self._shift:
            result = value / 1000
        elif self._ctrl:
            result = round(value / 50)

        if self._is_circle:
            self.circle(context, result)
        else:
            self.line(context, result)

        return {'FINISHED'}

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value: int):
        if value < 2:
            return

        self._count = value

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        self._shift = event.shift
        self._ctrl = event.ctrl
        self.drawer.set_active('Shift', event.shift)
        self.drawer.set_active('Ctrl', event.ctrl)

        if event.type == 'MOUSEMOVE':  # Apply
            self._mouse_pos = (event.mouse_x, event.mouse_y)
            self.execute(context)
        elif event.type == 'WHEELUPMOUSE':
            self.count += 1
            self.execute(context)
        elif event.type == 'WHEELDOWNMOUSE':
            self.count -= 1
            self.execute(context)
        elif event.type == 'X':
            self._dir = 0
            self.execute(context)
        elif event.type == 'Y':
            self._dir = 1
            self.execute(context)
        elif event.type == 'Z':
            self._dir = 2
            self.execute(context)
        elif event.type == 'C' and event.value == 'PRESS':
            self._is_circle = not self._is_circle
            self.drawer.set_active('C', self._is_circle)
            self.create_empty()
            self.execute(context)
        elif event.type == 'LEFTMOUSE':  # Confirm
            self.drawer.deactivate()
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            context.active_object.modifiers.remove(self._mod)

            if self._empty:
                bpy.data.objects.remove(self._empty)
            self.drawer.deactivate()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self._init_loc_x = context.object.location.x
        self._mouse_start_pos = (event.mouse_x, event.mouse_y)
        self._mouse_pos = (event.mouse_x, event.mouse_y)
        self.create_empty()

        self.init(context.active_object)
        self.execute(context)

        self.drawer = Drawer()
        self.drawer.activate()

        self.drawer.add_shortcut('X/Y/Z', 'Array Direction')
        self.drawer.add_shortcut('C', 'Radial Array')
        self.drawer.add_shortcut('Wheel Down/Up', 'Array Count')
        self.drawer.add_shortcut('Shift', 'Slow Mode')
        self.drawer.add_shortcut('Ctrl', 'Increment By One')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

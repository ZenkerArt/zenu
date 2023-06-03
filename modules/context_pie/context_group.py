import types
from abc import ABC
from typing import Type, Iterable, Callable

import bpy.types

DrawerFunction = Callable[[bpy.types.Context, bpy.types.UILayout], None]


class Drawer(ABC):

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        pass

    def draw_submenu(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        pass

    def is_mode(self, text: str):
        if not bpy.context or not bpy.context.active_object:
            return False
        return bpy.context.active_object.mode == text

    @property
    def is_object_mode(self):
        return self.is_mode('OBJECT')

    @property
    def is_edit(self):
        return self.is_mode('EDIT')

    @property
    def is_pose(self):
        return self.is_mode('POSE')

    @property
    def is_sculpt(self):
        return self.is_mode('SCULPT')

    @property
    def is_vertex_paint(self):
        return self.is_mode('VERTEX_PAINT')

    @property
    def is_weight_paint(self):
        return self.is_mode('WEIGHT_PAINT')

    @property
    def is_texture_paint(self):
        return self.is_mode('TEXTURE_PAINT')

    @property
    def is_particle_edit(self):
        return self.is_mode('PARTICLE_EDIT')

    @property
    def is_edit_gpencil(self):
        return self.is_mode('EDIT_GPENCIL')


class DrawerFunctionWrap(Drawer):
    func: DrawerFunction

    def __init__(self, func: DrawerFunction):
        self.func = func

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        self.func(context, layout)


class ContextGroup:
    _name: str
    _drawer: list[Drawer]

    def __init__(self, name: str):
        self._name = name
        self._drawer = []

    def register_class(self, cls: Type[Drawer] | DrawerFunction):
        if isinstance(cls, types.FunctionType):
            self._drawer.append(DrawerFunctionWrap(cls))
            return

        self._drawer.append(cls())

    def register_classes(self, cls: Iterable[Drawer | DrawerFunction]):
        for c in cls:
            self.register_class(c)

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        for i in self._drawer:
            if not i.poll(context):
                continue
            i.draw(context, layout)

    def draw_submenu(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        for i in self._drawer:
            if not i.poll(context):
                continue
            i.draw_submenu(context, layout)

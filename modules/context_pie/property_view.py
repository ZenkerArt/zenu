from typing import Callable

import bpy


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

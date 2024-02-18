from typing import Callable, Any

import bpy


class OperatorView:
    _func: Callable[[bpy.types.Object], bool]
    _name: str
    _ops: str
    _obj: bpy.types.Object
    _vars: dict[str, Any] = {}
    layout: bpy.types.UILayout

    def __init__(self,
                 obj: bpy.types.Object, ops: str,
                 func: Callable[[bpy.types.Object], bool] = None,
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

        typed, operator = self._ops.split('.')

        if not getattr(getattr(bpy.ops, typed), operator).poll():
            return

        if self._func is not None and not self._func(self._obj):
            return

        if self._name:
            op = layout.operator(self._ops, text=self._name)
        else:
            op = layout.operator(self._ops)

        for key, value in self._vars.items():
            setattr(op, key, value)

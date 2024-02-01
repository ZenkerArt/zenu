from abc import ABC, abstractmethod
from typing import Optional, Any, Iterable

import bpy.types


class MenuItem(ABC):
    _title: str = None

    @abstractmethod
    def draw(self, layout: bpy.types.UILayout, obj: Any):
        pass


class OperatorItem(MenuItem):
    _op: str
    _vars: dict[str, str] = None
    _text: str

    def __init__(self, op: str, text: str = None, vars: dict[str, str] = None):
        self._op = op
        self._title = text

        self._vars = vars

        if vars is None:
            self._vars = {}


    def draw(self, layout: bpy.types.UILayout, obj: Any):
        typed, operator = self._op.split('.')

        if not getattr(getattr(bpy.ops, typed), operator).poll():
            return

        op = layout.operator(self._op, text=self._title)

        if self._vars is not None:
            for key, value in self._vars.items():
                setattr(op, key, value)


class PropertyItem(MenuItem):
    _op: str

    def __init__(self, op: str, text: str = ''):
        self._op = op
        self._title = text

    def draw(self, layout: bpy.types.UILayout, obj: Any):
        layout.prop(obj, self._op, text=self._title)


Item = OperatorItem | PropertyItem

class MenuGroup:
    _operators: list[OperatorItem]
    _properties: list[PropertyItem]
    _groups: list['MenuGroup']

    def __init__(self):
        self._operators = []
        self._properties = []
        self._groups = []

    @property
    def all(self) -> list[MenuItem]:
        return [*self._properties, *self._operators]

    @property
    def operators(self):
        return self._operators

    @property
    def properties(self):
        return self._properties

    @property
    def groups(self):
        return self._groups

    def add(self, operator: OperatorItem | PropertyItem):
        if isinstance(operator, OperatorItem):
            self._operators.append(operator)
        else:
            self._properties.append(operator)

    def add_list(self, items: Iterable[Item]):
        for item in items:
            self.add(item)

    def create_group(self) -> 'MenuGroup':
        menu_group = MenuGroup()
        self._groups.append(menu_group)
        return menu_group

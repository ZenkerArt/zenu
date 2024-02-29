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
    _icon: str
    _id: str

    def __init__(self,
                 op: str | bpy.types.Operator,
                 text: str = None,
                 icon: str = None,
                 vars: dict[str, str] = None,
                 op_id: str = ''):
        if isinstance(op, bpy.types.Operator):
            self._op = op.bl_idname
        else:
            self._op = op

        self._id = op_id or self._op
        self._title = text

        self._vars = vars
        self._icon = icon

        if vars is None:
            self._vars = {}

    @property
    def id(self):
        return self._id

    def __eq__(self, other):
        if hasattr(other, 'id'):
            return self.id == other.id

        if isinstance(other, str):
            return self.id == other

        return False

    def draw(self, layout: bpy.types.UILayout, obj: Any):
        typed, operator = self._op.split('.')

        if not getattr(getattr(bpy.ops, typed), operator).poll():
            return

        if self._icon:
            op = layout.operator(self._op, text=self._title, icon=self._icon)
        else:
            op = layout.operator(self._op, text=self._title)

        if self._vars is not None:
            for key, value in self._vars.items():
                setattr(op, key, value)


class OperatorItemList(MenuItem):
    _id: str
    _operators: list[OperatorItem]

    def __init__(self, op_id: str, operators: list[OperatorItem]):
        self._id = op_id
        self._operators = operators

    @property
    def id(self):
        return self._id

    def __eq__(self, other):
        if hasattr(other, 'id'):
            return self.id == other.id

        if isinstance(other, str):
            return self.id == other

        return False

    def draw(self, layout: bpy.types.UILayout, obj: Any):
        row = layout.row(align=True)
        for op in self._operators:
            op.draw(row, obj)


class PropertyItem(MenuItem):
    _prop: str

    def __init__(self, prop: str, text: str = ''):
        self._prop = prop
        self._title = text

    @property
    def id(self):
        return self._prop

    def __eq__(self, other):
        if hasattr(other, 'id'):
            return self.id == other.id

        if isinstance(other, str):
            return self.id == other

        return False

    def draw(self, layout: bpy.types.UILayout, obj: Any):
        layout.prop(obj, self._prop, text=self._title)


class MenuGroup:
    _operators: list[OperatorItem | OperatorItemList]
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

    def add(self, operator: OperatorItem | PropertyItem | OperatorItemList):
        operator_exists = operator in self._operators
        property_exists = operator in self._properties
        if property_exists or operator_exists:
            return

        if isinstance(operator, OperatorItem) or isinstance(operator, OperatorItemList):
            self._operators.append(operator)
        elif isinstance(operator, PropertyItem):
            self._properties.append(operator)

    def add_list(self, items: Iterable[PropertyItem | OperatorItem | OperatorItemList]):
        for item in items:
            self.add(item)

    def create_group(self) -> 'MenuGroup':
        menu_group = MenuGroup()
        self._groups.append(menu_group)
        return menu_group

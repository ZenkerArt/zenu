import bpy

from .items import BaseItem, OperatorItem, create_item_from_dct


class PiePanel:
    _ID: str
    _data: dict[str, BaseItem]

    def __init__(self, ID: str):
        self._ID = ID
        self._data = {}

    @property
    def id(self):
        return self._ID

    def add_property(self, op: str, text: str = None, icon: str = None):
        self._data[op] = OperatorItem(
            path=op,
            text=text,
            icon=icon
        )

    def add_operator(self, op: str, text: str = None, icon: str = None, args: dict[str, any] = None):
        self._data[op] = OperatorItem(
            path=op,
            text=text,
            icon=icon,
            args=args
        )

    def _draw_operator(self, operator_item: OperatorItem, layout: bpy.types.UILayout):
        operator_args = {}

        if operator_item.text:
            operator_args['text'] = operator_item.text

        if operator_item.icon:
            operator_args['icon'] = operator_item.icon

        op = layout.operator(operator_item.path, **operator_args)

        for key, value in operator_item.args.items():
            setattr(op, key, value)

    def draw(self, layout: bpy.types.UILayout):
        for data in self._data.values():
            if isinstance(data, OperatorItem):
                self._draw_operator(data, layout)

    def to_dict(self):
        return {
            'id': self._ID,
            'data': {key: value.to_dict() for key, value in self._data.items()}
        }

    def from_dict(self, dct):
        self._data = {key: create_item_from_dct(item) for key, item in dct['data'].items()}
        return self

    @property
    def operators(self):
        return list(self._data.values())
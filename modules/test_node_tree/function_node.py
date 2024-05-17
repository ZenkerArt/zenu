import inspect
from typing import Any

import bpy
from mathutils import Vector
from typing import TYPE_CHECKING
from .base_node import BaseNode, NodeContext
from .node_store import socket_store

if TYPE_CHECKING:
    from . import TestNodeTree


class FunctionNodeResult:
    pass


class FunctionNode(BaseNode):
    node_context: NodeContext
    @staticmethod
    def _get_socket_type(typ: Any):
        value = socket_store.get_socket_name_by_type(typ)

        if value is None:
            raise RuntimeError(f'Type is not register "{typ.__name__}"')

        return value.socket_name

    @property
    def node_tree(self) -> 'TestNodeTree':
        return bpy.context.space_data.edit_tree

    def init(self, context: bpy.types.Context):
        return_type = None

        for key, typ in inspect.get_annotations(self.call).items():
            if key == 'return':
                return_type = typ
                continue
            self.input(self._get_socket_type(typ), key)

        if return_type is not None:
            if issubclass(return_type, FunctionNodeResult):
                for key, typ in inspect.get_annotations(return_type).items():
                    self.output(self._get_socket_type(typ), key)
                return

            typ = self._get_socket_type(return_type)
            self.output(typ, 'Out')

    def call(self, *args, **kwargs) -> Any:
        pass

    def execute(self, context: bpy.types.Context, node_context: NodeContext):
        props = node_context.props
        self.node_context = node_context
        dct = {}

        for key, typ in inspect.get_annotations(self.call).items():
            if key == 'return': continue
            dct[key] = props.get(key)
        return self.call(**dct)

from typing import Any

import bpy
from . import socket_store
from .base_node import BaseNode, NodeContext


class PropertyNode(BaseNode):
    output_type: Any
    output_name: str = 'None'

    def init(self, context: bpy.types.Context):
        name = socket_store.get_socket_name_by_type(self.output_type)
        self.output(name.socket_name, self.output_name)

    def execute(self, context: bpy.types.Context, node_context: NodeContext):
        return node_context.attributes[self.output_name]

import bpy
from . import socket_store
from .base_node import BaseNode


class MenuNode(BaseNode):
    def menu_items(self):
        return {''}

    def init(self, context: bpy.types.Context):
        name = socket_store.get_socket_name_by_type(self.output_type)

        self.output(name.socket_name, self.output_name)

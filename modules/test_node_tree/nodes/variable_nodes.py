import bpy
from bpy.types import NodeSocket
from .. import FunctionNode
from ..node_store import ZenuSocket, socket_store


class ZENU_ND_set_variable(FunctionNode):
    bl_label = 'Set Variable'

    def init(self, context: bpy.types.Context):
        self.input('NodeSocketString', 'name')
        self.input('ZenuUnknownSocket', 'unknown')

    def update(self):
        socket = self.inputs[1]
        i: bpy.types.NodeLink
        for i in socket.links:
            socket_id = type(i.from_socket).__name__

            if hasattr(i.from_socket, 'bl_idname'):
                socket_id = i.from_socket.bl_idname


            inp = self.input(socket_id, 'value')
            self.node_tree.links.new(inp, i.from_socket)
            self.inputs.remove(socket)
            # print()
        # print('I awdawd')

    def call(self):
        pass


class ZenuUnknownSocket(NodeSocket):
    bl_label = "Unknown"

    def draw(self, context, layout, node, text):
        pass

    # Socket color
    @classmethod
    def draw_color_simple(cls):
        return (.2, .2, .2, 1)


nodes = (
    ZENU_ND_set_variable,
)

sockets = (
    ZenuSocket(
        socket=ZenuUnknownSocket,
        types=tuple()
    ),
)

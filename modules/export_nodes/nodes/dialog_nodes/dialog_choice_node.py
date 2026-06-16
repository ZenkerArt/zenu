import bpy

from . import BaseDialogNode
from ... import node_categories
from ...sockets.dialog_socket import DialogSocketType, DialogContext


class ZENU_OT_add_dialog_variant(bpy.types.Operator):
    bl_label = 'Add Dialog Variant'
    bl_idname = 'zenu.add_dialog_variant'

    node_system: bpy.props.StringProperty()
    node: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        node: DialogChoiceNode = bpy.data.node_groups[self.node_system].users[self.node]

        node.add_socket()

        return {'FINISHED'}


class DialogChoiceNode(BaseDialogNode):
    bl_idname = "DialogChoiceNode"
    bl_label = "Dialog Choice"
    hash: bpy.props.StringProperty()
    dialog_type = 'choice'
    has_order = True

    def draw_buttons(self, context, layout):
        socket: DialogSocketType = self.outputs['variants']

        nodes = [link.to_node for link in socket.links]

        ns = sorted(nodes, key=lambda node: node.order)

        for node in reversed(ns):
            box = layout.box()
            box.label(text=node.dialog_text)

    def init(self, context):
        self.inputs.new(DialogSocketType.bl_idname, 'dialog')
        self.outputs.new(DialogSocketType.bl_idname, 'variants')

    def compute(self, **inputs):
        socket: DialogContext = inputs['dialog']
        for link in self.outputs['variants'].links:
            socket.add_link(self, link.to_node)

        return {
            'variants': inputs['dialog']
        }


reg, unreg = bpy.utils.register_classes_factory((
    DialogChoiceNode,
    ZENU_OT_add_dialog_variant
))


def register():
    node_categories.dialog.add_node(DialogChoiceNode)
    reg()


def unregister():
    unreg()

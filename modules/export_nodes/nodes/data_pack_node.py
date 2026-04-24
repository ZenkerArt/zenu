import bpy
from .base_node import BaseNode
from .. import ObjectSocketType, node_categories


class DataPackNode(BaseNode):
    bl_idname = "DataPackNode"
    bl_label = "Data Pack"

    my_enum: bpy.props.EnumProperty(
        name="Pack Type",
        items=[
            ('MODEL', "Model", ""),
            ('ANIMATION', "Animation (Not implemented)", ""),
        ],
        default='MODEL'
    )

    def draw_buttons(self, context, layout):
        layout.label(text='Export Type')
        layout.prop(self, "my_enum", text='')
        # op = layout.operator(ZENU_OT_add_socket.bl_idname)
        # op.node_system = self.id_data.name
        # op.name = self.name

    def init(self, context):
        self.inputs.new(ObjectSocketType.bl_idname, "obj")

reg, unreg = bpy.utils.register_classes_factory((
    DataPackNode,
))


def register():
    reg()
    node_categories.general.add_node(DataPackNode)


def unregister():
    unreg()

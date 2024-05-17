import bpy
from mathutils import Vector
from .. import PropertyNode, FunctionNode, socket_store
from ..base_node import BaseNode


class ZENU_ND_execute_node(BaseNode):
    bl_label = 'Output'
    value: bpy.props.FloatProperty()

    def init(self, context):
        self.input('NodeSocketFloat', 'B')

    def draw_buttons(self, context, layout: bpy.types.UILayout):
        layout.prop(self, 'value')
        layout.operator('zenu.execute_node_system')


class ZENU_ND_position(PropertyNode):
    bl_label = 'Position'
    output_type = Vector
    output_name = 'position'


class ZENU_ND_rotation(PropertyNode):
    bl_label = 'Rotation'
    output_type = Vector
    output_name = 'rotation'


class ZENU_ND_scale(PropertyNode):
    bl_label = 'Scale'
    output_type = Vector
    output_name = 'scale'


def attr_transfer_enum(self, context):
    return tuple((soc.socket_name, soc.socket_name, '') for soc in socket_store.sockets)


class ZENU_ND_attr_transfer(FunctionNode):
    bl_label = 'Attribute Transfer'
    enum: bpy.props.EnumProperty(items=attr_transfer_enum)

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        layout.prop(self, 'enum', text='')

    def call(self):
        pass


nodes = (
    ZENU_ND_execute_node,
    ZENU_ND_position,
    ZENU_ND_rotation,
    ZENU_ND_scale,
    ZENU_ND_attr_transfer
)

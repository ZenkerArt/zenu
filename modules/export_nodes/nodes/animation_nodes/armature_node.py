import bpy
from ..base_node import BaseNode
from ... import node_categories
from ...sockets.armature_socket import ArmatureTypeSocket, ArmatureSocketResponse
from ...utils import object_filter_static, ObjectTypes

class ArmatureNode(BaseNode):
    bl_idname = "ArmatureNode"
    bl_label = "Armature"

    armature: bpy.props.PointerProperty(type=bpy.types.Object, poll=object_filter_static(ObjectTypes.ARMATURE))
    animation_slot: bpy.props.StringProperty()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'armature', text='')
        layout.prop(self, 'animation_slot', text='', placeholder='Action Slot Name')

    def init(self, context):
        self.outputs.new(ArmatureTypeSocket.bl_idname, 'armature')

    def compute(self, **inputs):
        return {
            'armature': ArmatureSocketResponse(
                armature=self.armature,
                action_slot_name=self.animation_slot
            )
        }


reg, unreg = bpy.utils.register_classes_factory((
    ArmatureNode,
))


def register():
    node_categories.animation.add_node(ArmatureNode)
    reg()


def unregister():
    unreg()

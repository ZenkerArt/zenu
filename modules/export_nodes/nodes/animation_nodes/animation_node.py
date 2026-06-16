import bpy
from ..base_node import BaseNode
from ... import node_categories


class AnimationNode(BaseNode):
    bl_idname = "AnimationNode"
    bl_label = "Animation"

    action: bpy.props.PointerProperty(type=bpy.types.Action)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'action', text='')
        action: bpy.types.Action = self.action

        # layout.label(text=action.name)

    def init(self, context):
        pass


reg, unreg = bpy.utils.register_classes_factory((
    AnimationNode,
))


def register():
    node_categories.animation.add_node(AnimationNode)
    reg()


def unregister():
    unreg()

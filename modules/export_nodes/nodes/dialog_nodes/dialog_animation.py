from dataclasses import dataclass

import bpy

from . import BaseDialogNode
from ... import node_categories
from ...sockets.dialog_modifier import DialogModifierSocketType, DialogModifierStack, DialogModifier

@dataclass
class DialogAnimationModifier(DialogModifier):
    action: bpy.types.Action
    sound: str

class DialogAnimationNode(BaseDialogNode):
    bl_idname = "DialogAnimationNode"
    bl_label = "Dialog Animation"

    action: bpy.props.PointerProperty(type=bpy.types.Action)
    # sound: bpy.props.PointerProperty(type=bpy.types.Sound)
    sound: bpy.props.StringProperty()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'action', text='')
        layout.prop_search(self, 'sound', context.scene.sequence_editor, 'strips', text='')

    def init(self, context):
        self.outputs.new(DialogModifierSocketType.bl_idname, 'modifier')
        self.inputs.new(DialogModifierSocketType.bl_idname, 'modifier')

    def compute(self, **inputs):
        print(inputs)
        # mod_stack: DialogModifierStack = inputs['_context'].get('mod_stack')
        # mod_stack.add_mod(DialogAnimationModifier(
        #     action=self.action,
        #     sound=self.sound
        # ))
        return {}


reg, unreg = bpy.utils.register_classes_factory((
    DialogAnimationNode,
))


def register():
    node_categories.dialog.add_node(DialogAnimationNode)
    reg()


def unregister():
    unreg()

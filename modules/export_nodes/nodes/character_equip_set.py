import bpy
from .base_node import BaseNode
from .. import node_categories
from ..sockets import CharacterEquipTypeSocket


class CharacterEquipSetList(list):
    name: str

    def __init__(self, name: str, lst):
        self.name = name
        super().__init__(lst)


class CharacterEquipSet(BaseNode):
    bl_idname = "CharacterEquipSet"
    bl_label = "Character Equipment Set"

    name: bpy.props.StringProperty()

    def draw_buttons(self, context, layout):
        box = layout.box()
        box.label(text='Name')
        box.prop(self, 'name')

    def init(self, context):
        self.inputs.new(CharacterEquipTypeSocket.bl_idname, 'equip', use_multi_input=True)
        self.outputs.new(CharacterEquipTypeSocket.bl_idname, 'equip')

    def compute(self, **inputs):
        return {
            'equip': CharacterEquipSetList(self.name, inputs['equip'])
        }


reg, unreg = bpy.utils.register_classes_factory((
    CharacterEquipSet,
))


def register():
    node_categories.character_equip.add_node(CharacterEquipSet)
    reg()


def unregister():
    unreg()

import bpy

from .base_node import BaseNode
from .. import node_categories
from ..sockets.character_equipment_socket import CharacterEquipTypeSocket, CharacterEquipData
from ..sockets.object_socket import ObjectSocketType
from ..utils import object_filter_static, ObjectTypes


class CharacterEquip(BaseNode):
    bl_idname = "CharacterEquip"
    bl_label = "Character Equipment"

    parent_type: bpy.props.EnumProperty(items=(
        ('BONE', 'Bone', ''),
        ('WEIGHT', 'Weight', ''),
    ))

    bone_name: bpy.props.StringProperty()
    armature: bpy.props.PointerProperty(type=bpy.types.Object, poll=object_filter_static(ObjectTypes.ARMATURE))
    name: bpy.props.StringProperty()

    def draw_buttons(self, context, layout):
        obj = self.inputs['equipment_object']
        box = layout.box()

        box.label(text='Character Armature')
        box.prop(self, 'armature', text='', placeholder='Character Armature')

        if self.armature is None:
            return
        box = layout.box()
        box.label(text='Parent')
        box.row().prop(self, 'parent_type', expand=True)

        if self.parent_type == 'BONE':
            box.prop_search(self, 'bone_name', search_data=self.armature.data, search_property='bones', text='')

        box.label(text='Equipment Name')
        box.prop(self, 'name', text='', placeholder='Equipment Name')

    def init(self, context):
        self.outputs.new(CharacterEquipTypeSocket.bl_idname, "character_equipment")

        socket = self.inputs.new(ObjectSocketType.bl_idname, "equipment_object")
        socket.filter_type = ObjectTypes.MESH

    def compute(self, **inputs):
        return {
            'character_equipment': CharacterEquipData(
                name=self.name,
                armature=self.armature,
                object=inputs['equipment_object'],
                data={
                    'parentType': self.parent_type,
                    'boneName': self.bone_name
                }
            )
        }


reg, unreg = bpy.utils.register_classes_factory((
    CharacterEquip,
))


def register():
    reg()
    node_categories.character_equip.add_node(CharacterEquip)


def unregister():
    unreg()

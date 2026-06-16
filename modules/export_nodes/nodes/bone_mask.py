from dataclasses import dataclass
from json import dumps, loads, JSONDecodeError

import bpy
from .base_node import BaseNode
from .. import node_categories
from ..sockets.mask_socket import MaskTypeSocket
from ..utils import object_filter_static, ObjectTypes


@dataclass
class MaskedBone:
    name: str


class ZENU_OT_bone_mask_set_from_selection(bpy.types.Operator):
    bl_label = 'Set From Selection'
    bl_idname = 'zenu.bone_mask_set_from_selection'

    node_tree: bpy.props.StringProperty()
    node: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        node_tree = bpy.data.node_groups[self.node_tree]
        node = node_tree.users[self.node]

        bone_list = []

        for bone in node.armature.pose.bones:
            bone: bpy.types.PoseBone

            if not bone.select: continue

            bone_list.append(bone.name)

        node.bone_mask = dumps(bone_list)
        return {'FINISHED'}


class BoneMask(BaseNode):
    bl_idname = "BoneMask"
    bl_label = "Bone Mask"

    object_with_armature: bpy.props.PointerProperty(type=bpy.types.Object, poll=object_filter_static(ObjectTypes.MESH))
    bone_mask: bpy.props.StringProperty()

    def get_armature(self, obj: bpy.types.Object) -> bpy.types.Object | None:
        for mod in obj.modifiers:
            mod: bpy.types.Modifier
            if mod.type != 'ARMATURE': continue
            return mod.object
        return None

    @property
    def armature(self):
        return self.get_armature(self.object_with_armature)

    def draw_buttons(self, context, layout):
        box = layout.box()
        box.label(text='Object')
        box.prop(self, 'object_with_armature', text='')

        obj: bpy.types.Object = self.object_with_armature

        if obj is None:
            return

        armature = self.armature

        if armature is None:
            return

        op = layout.operator(ZENU_OT_bone_mask_set_from_selection.bl_idname)
        op.node_tree = self.id_data.name
        op.node = self.name

        layout.label(text='Masked Bone')

        box = layout.box()
        try:
            lst = loads(self.bone_mask)
            for i in lst:
                box.label(text=i)

            if not lst:
                box.label(text='Nothing masked')
        except JSONDecodeError:
            box.label(text='Nothing masked')

    def init(self, context):
        self.outputs.new(MaskTypeSocket.bl_idname, 'Mask')


reg, unreg = bpy.utils.register_classes_factory((
    BoneMask,
    ZENU_OT_bone_mask_set_from_selection
))


def register():
    node_categories.general.add_node(BoneMask)
    reg()


def unregister():
    unreg()

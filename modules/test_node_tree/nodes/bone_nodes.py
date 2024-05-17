from dataclasses import dataclass

import bpy
from bpy_types import NodeSocket
from mathutils import Vector
from ..property_node import PropertyNode
from ...rig import MetaBoneData
from ....utils import is_type
from ..base_node import BaseNode, NodeContext
from .. import FunctionNodeResult, FunctionNode
from ..node_store import ZenuSocket


@dataclass()
class ArmatureInfo:
    obj: bpy.types.Object
    arm: bpy.types.Armature


class ZenuBoneSocket(NodeSocket):
    bl_label = "Pose Bone Socket"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    # Socket color
    @classmethod
    def draw_color_simple(cls):
        return (0.0, 1, 1, .8)


class ZenuArmatureSocket(NodeSocket):
    bl_label = 'Armature Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    # Socket color
    @classmethod
    def draw_color_simple(cls):
        return (0, 1, 0, 1)


@dataclass
class GetBoneResult(FunctionNodeResult):
    bone: bpy.types.PoseBone


class ZENU_ND_get_armature(FunctionNode):
    bl_label = 'Get Armature'
    target: bpy.props.PointerProperty(type=bpy.types.Object, poll=lambda _, obj: is_type(obj, bpy.types.Armature))

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        layout.prop(self, 'target', text='')

    def call(self) -> ArmatureInfo:
        return ArmatureInfo(
            obj=self.target,
            arm=self.target.data
        )


class ZENU_ND_get_bone(FunctionNode):
    bl_label = 'Get Bone'

    def call(self, name: str, arm: ArmatureInfo) -> GetBoneResult:
        bone = arm.obj.pose.bones[name]
        props = self.node_context.attributes
        props['position'] = bone.location
        props['rotation'] = bone.rotation_euler
        props['scale'] = bone.scale
        return GetBoneResult(
            bone=bone
        )


class ZENU_ND_get_bone_pos(FunctionNode):
    bl_label = 'Get Bone Position'
    is_global: bpy.props.BoolProperty(name='Global')

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        layout.prop(self, 'is_global')

    def call(self, bone: bpy.types.PoseBone) -> Vector:
        if self.is_global:
            obj: bpy.types.Object = bone.id_data
            return obj.matrix_world @ (bone.matrix @ bone.location)

        return bone.location


class ZENU_ND_get_position(PropertyNode):
    bl_label = 'Get Position'
    output_type = Vector
    output_name = 'position'
    property_name = 'location'


class ZENU_ND_set_bone_pos(FunctionNode):
    bl_label = 'Set Bone Position'

    def call(self, bone: bpy.types.PoseBone, position: Vector) -> bpy.types.PoseBone:
        bone.location = position
        # print(bone.location)

        return bone


class ZENU_ND_transform_bone(FunctionNode):
    bl_label = 'Transform Bone'

    def call(self, bone: bpy.types.PoseBone, position: Vector, rotation: Vector, scale: Vector) -> bpy.types.PoseBone:
        bone.location = position
        bone.rotation_euler = rotation
        bone.scale = scale
        return bone


class ZENU_ND_look_at(FunctionNode):
    bl_label = 'Look At'

    def call(self, bone1: bpy.types.PoseBone, bone2: bpy.types.PoseBone) -> bpy.types.PoseBone:
        print(bone1.location)
        return bone1


nodes = (
    ZENU_ND_get_armature,
    ZENU_ND_get_bone,
    ZENU_ND_get_bone_pos,
    ZENU_ND_set_bone_pos,
    ZENU_ND_get_position,
    ZENU_ND_transform_bone,
)

sockets = (
    ZenuSocket(
        socket=ZenuBoneSocket,
        types=(bpy.types.PoseBone,)
    ),
    ZenuSocket(
        socket=ZenuArmatureSocket,
        types=(ArmatureInfo,)
    ),
)

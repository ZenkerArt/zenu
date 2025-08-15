import math

import bpy

from ... import MetaBoneData
from ...rigs import RigModule
from ...bone_utils import bone_get_head, bone_connect
from mathutils import Vector, Matrix


class StandardIK(RigModule):
    rig_name = 'Standard IK'
    target: str
    target_pole: str
    ik: str

    def create_ik_layer(self, bone1: MetaBoneData, bone2: MetaBoneData):
        target = bone1.clone(name='Target', prefix='IK-')
        target.head += bone1.forward_vector * bone1.edit_bone.length
        target.tail += bone1.forward_vector * bone1.edit_bone.length / 2

        tail = bone2.edit_bone.tail
        is_invert = bone2.forward_vector.y > 0

        invert = 1 if is_invert else -1

        target_pole = bone1.clone(name='PoleTarget', prefix='IK-')
        target_pole.head = tail + Vector((0, .4 * invert, 0))
        target_pole.tail = tail + Vector((0, .6 * invert, 0))

        bone2.edit_bone.roll = -math.pi / 2

        b1 = bone1.clone(bone1.name, prefix='IK-')
        b2 = bone2.clone(bone2.name, prefix='IK-')
        bone_connect([b2, b1], use_connect=False)

        return target.name, target_pole.name, b1.name

    def execute_edit(self, context: bpy.types.Context):
        bone = self.bone
        parent = bone.parent

        self.target, self.target_pole, self.ik = self.create_ik_layer(bone, parent)

    def execute_pose(self, context: bpy.types.Context):
        bone = self.bone
        parent = bone.parent

        constraint: bpy.types.KinematicConstraint = bone.obj.pose.bones[self.ik]._constraints.new('IK')
        constraint.chain_count = 2

        constraint.target = self.bone.obj
        constraint.subtarget = self.target

        constraint.pole_target = self.bone.obj
        constraint.pole_subtarget = self.target_pole
        constraint.pole_angle = math.pi / 2

import math
from abc import abstractmethod
from dataclasses import dataclass

import bpy
from ... import MetaBoneData
from ...bone_utils import bone_create_lerp, bone_subdivide, bone_connect, bone_clone
from ...rigs import RigModule
from ...shapes import ShapesEnum

TWEAKER_POSTFIX = '_TWEAKER'
FK_POSTFIX = '_FK'


@dataclass
class TweakerConnect:
    start: str
    end: str
    tweaker: str
    is_bbone: bool = False
    bbone_segments: int = 1


@dataclass
class ArmatureConnect:
    tweaker: str
    bones: list[str]


class TentacleRig(RigModule):
    rig_name = 'Tentacle Rig'
    parents: list[tuple[str, str]]
    bbone_parent: list[tuple[str, str]]
    tweaker_connects: list[TweakerConnect]
    armature_connects: list[ArmatureConnect]

    def init(self):
        self.bbone_parent = []
        self.parents = []
        self.tweaker_connects = []
        self.armature_connects = []

    def draw(self, context: bpy.types.Context):
        pass

    def connect_tweaker(self, bone_start: bpy.types.EditBone, bone_end: bpy.types.EditBone,
                        is_bbone: bool = False) -> bpy.types.EditBone:
        tweaker_center = bone_create_lerp(bone_start, 1, postfix=TWEAKER_POSTFIX)
        tweaker_center.length = tweaker_center.length / 6
        bone_end.parent = tweaker_center
        tweaker_center.use_deform = False
        if is_bbone:
            self.styles.add(tweaker_center.name, ShapesEnum.ArrowTwoSide)
            self.coll.add_ik(tweaker_center)
        else:
            self.styles.add(tweaker_center.name, ShapesEnum.SphereDirWire)
            self.coll.add_tweakers(tweaker_center)

        self.tweaker_connects.append(TweakerConnect(
            start=bone_start.name,
            end=bone_end.name,
            tweaker=tweaker_center.name,
            is_bbone=is_bbone
        ))

        if not is_bbone:
            return tweaker_center

        bone_end.inherit_scale = 'NONE'
        bone_start.inherit_scale = 'NONE'

        bone_end.bbone_custom_handle_start = tweaker_center
        bone_end.bbone_segments = 6
        bone_start.bbone_custom_handle_end = tweaker_center
        bone_start.bbone_segments = 6

        bone_start.bbone_handle_type_end = 'TANGENT'
        bone_start.bbone_handle_type_start = 'TANGENT'
        bone_end.bbone_handle_type_end = 'TANGENT'
        bone_end.bbone_handle_type_start = 'TANGENT'
        return tweaker_center

    def create_end_tweaker(self, bone: bpy.types.EditBone, factor: float = 1):
        tweaker = bone_create_lerp(bone, factor, postfix=TWEAKER_POSTFIX + '_TIP')
        tweaker.length = tweaker.length / 6
        tweaker.use_deform = False

        if factor <= 0:
            bone.parent = tweaker
        else:
            self.bbone_parent.append((bone.name, tweaker.name))
        self.styles.add(tweaker.name, ShapesEnum.SphereDirWire)

        return tweaker

    def execute_edit(self, context: bpy.types.Context):
        self.bbone_parent.clear()
        self.parents.clear()
        self.tweaker_connects.clear()
        self.armature_connects.clear()

        start_bones = [self.bone.edit_bone]
        start_bones.extend((i.edit_bone for i in self.bone.parent_list))

        prev_bone = start_bones[-1]
        prev_sub_bone = None
        for current_bone in start_bones:
            current_bone.use_deform = False
            current_bone.use_connect = False
            self.coll.add_mch(current_bone)

            if prev_bone:
                self.connect_tweaker(current_bone, prev_bone, is_bbone=True)

                pb = None

                bones = bone_subdivide(current_bone, 3)

                for bone in bones:
                    self.coll.add_deform(bone)
                    if pb is None:
                        pb = bone
                        continue

                    tweaker = self.connect_tweaker(pb, bone)

                    self.armature_connects.append(ArmatureConnect(
                        bones=[current_bone.name],
                        tweaker=tweaker.name
                    ))

                    pb = bone

                tweaker = self.create_end_tweaker(pb)

                if prev_sub_bone:
                    prev_sub_bone.parent = tweaker

                    self.armature_connects.append(ArmatureConnect(
                        bones=[prev_bone.name, current_bone.name],
                        tweaker=tweaker.name
                    ))
                else:
                    self.armature_connects.append(ArmatureConnect(
                        bones=[current_bone.name],
                        tweaker=tweaker.name
                    ))

                prev_sub_bone = bones[0]

            prev_bone = current_bone

        # self.create_end_tweaker(start_bones[0])
        self.create_end_tweaker(start_bones[-1], 0)

    def execute_pose(self, context: bpy.types.Context):
        arm_obj = self.bone.obj

        def add_driver(bone: bpy.types.EditBone, prop: str):
            var = bone.driver_add(prop)
            driver = var.driver
            driver.expression = 'var - 1'
            variable = driver.variables.new()
            variable.type = 'TRANSFORMS'

            v = variable.targets[0]
            v.transform_space = 'LOCAL_SPACE'
            v.transform_type = 'SCALE_Y'

            return v

        for armature in self.armature_connects:
            tweaker = arm_obj.pose.bones[armature.tweaker]

            constraint: bpy.types.ArmatureConstraint = tweaker.constraints.new(type='ARMATURE')

            for bone in armature.bones:
                target = constraint.targets.new()
                target.target = arm_obj
                target.subtarget = bone

        for tweaker in self.tweaker_connects:
            bone_start = arm_obj.pose.bones[tweaker.start]
            bone_end = arm_obj.pose.bones[tweaker.end]
            bone_tweaker = arm_obj.pose.bones[tweaker.tweaker]

            constraint_start: bpy.types.StretchToConstraint = bone_start.constraints.new(type='STRETCH_TO')
            constraint_start.target = arm_obj
            constraint_start.subtarget = bone_tweaker.name

            if not tweaker.is_bbone:
                continue

            var_start = add_driver(bone_start, 'bbone_easeout')
            var_end = add_driver(bone_end, 'bbone_easein')

            var_start.id = arm_obj
            var_start.bone_target = bone_tweaker.name

            var_end.id = arm_obj
            var_end.bone_target = bone_tweaker.name

        for bbone in self.bbone_parent:
            bone_start = arm_obj.pose.bones[bbone[0]]
            bone_tweaker = arm_obj.pose.bones[bbone[1]]

            constraint_start: bpy.types.StretchToConstraint = bone_start.constraints.new(type='STRETCH_TO')
            constraint_start.target = arm_obj
            constraint_start.subtarget = bone_tweaker.name

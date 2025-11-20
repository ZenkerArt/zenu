from ast import Index
from asyncio import constants
from dataclasses import dataclass
from typing import Any
import bpy
from ..layers import BoneCollectorLayer, CopyConstraintLayer, RigComponentsLayer, StyleLayer, BoneCollectionLayer
from ..rig_lib import RigBone, RigComponent, RigContext
from ..rig_lib.bone_utils import bone_clone


@dataclass
class AimBone:
    aim: RigBone
    deform: RigBone | None
    target: RigBone


class Aim(RigComponent):
    name = 'Aim'
    bones: list[AimBone]

    def __init__(self):
        super().__init__()
        self.bones = []

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        pass

    def _create_bone(self, root: RigBone, children: list[RigBone]):
        root.edit.use_deform = False
        
        for bone in children:        
            bone_edit = bone.edit
            bone_dir = (bone_edit.head - bone_edit.tail).normalized()
            def_bone = None
            try:
                def_bone = bone_edit.children[0]
                bone_edit.use_deform = False
                def_bone.use_deform = True
            except IndexError:
                pass

            bone_target = bone_clone(bone_edit, f'TGT-AIM-{bone_edit.name}')
            bone_target.use_deform = False
            length = (bone_target.head - root.edit.head)

            bone_target.head -= bone_dir * length
            bone_target.tail = bone_target.head - (bone_dir * bone_edit.length)

            bone_edit.parent = root.edit.parent
            bone_target.parent = root.edit

            self.bones.append(AimBone(
                aim=bone,
                deform=self.convert_bone(def_bone).first_result,
                target=self.convert_bone(bone_target).first_result
            ))

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, layers: RigComponentsLayer):
        names = bones_collector.get_bones_by_type(self)
        for i in bones_collector.get_rig_bones_by_type(self):
            bone_edit = i.edit

            if bone_edit.name.startswith('TGT'):
                child = [i for i in bone_edit.children if i.name in names]
                self._create_bone(self.convert_bone(bone_edit).first_result, self.convert_bone(child).results)

    def execute_pose(self, context: RigContext, bones_collector: BoneCollectorLayer):
        for i in self.bones:
            aim = i.aim.pose
            target = i.target.pose

            constraint: bpy.types.DampedTrackConstraint = aim.constraints.new(
                'DAMPED_TRACK')

            constraint.target = i.target.arm
            constraint.subtarget = target.name
            
            if i.deform:
                deform = i.deform.pose
            
                constraint: bpy.types.CopyScaleConstraint = deform.constraints.new(
                    'COPY_SCALE')

                constraint.target = i.target.arm
                constraint.subtarget = target.name

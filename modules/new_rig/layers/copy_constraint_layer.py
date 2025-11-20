from collections import defaultdict
from dataclasses import dataclass
from email.policy import default
import bpy
from ..rig_lib import RigBone, RigContext, RigLayer


class ArmatureConst:
    _bones: list[tuple[bpy.types.Object, str, float]]

    def __init__(self, const: bpy.types.ArmatureConstraint):
        self._bones = []

        for target in const.targets:
            self.add_bone(target.target, target.subtarget, target.weight)

    def add_bone(self, obj: bpy.types.Object, name: str, weight: float):
        self._bones.append((
            obj, name, weight
        ))

    def apply_constraint(self, bone: RigBone):
        constraint: bpy.types.ArmatureConstraint = bone.pose.constraints.new(
            'ARMATURE')

        for (obj, name, weight) in self._bones:
            target = constraint.targets.new()
            target.target = bone.arm
            target.subtarget = name
            target.weight = weight

        return constraint

@dataclass
class CopyFrom:
    src: RigBone
    dst: RigBone
    replace: RigBone = None

class CopyConstraintLayer(RigLayer):
    _copy: list[CopyFrom]

    def __init__(self):
        self._copy = []

    def copy_from(self, src: RigBone, dst: RigBone, replace: RigBone = None):
        self._copy.append(CopyFrom(
            src=src,
            dst=dst,
            replace=replace
        ))
    
    def execute(self, context: RigContext):
        bpy.ops.object.mode_set(mode='POSE')

        for cop in self._copy:
            constraints: list[ArmatureConst] = []
            
            for con in cop.src.pose.constraints:
                if isinstance(con, bpy.types.ArmatureConstraint):
                    constraints.append(ArmatureConst(con))
                    continue
            
            for i in constraints:
                i.apply_constraint(cop.dst)

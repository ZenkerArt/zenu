from dataclasses import dataclass

from mathutils import Matrix
import bpy

@dataclass
class OvBone:
    armature_name: str
    bone_name: str

    @property
    def arm(self):
        return bpy.data.objects[self.armature_name]

    @property
    def bone(self):
        return self.arm.pose.bones[self.bone_name]

    @property
    def matrix_world(self):
        return self.arm.matrix_world @ self.bone.matrix

    @property
    def matrix_basis(self) -> Matrix:
        return self.bone.matrix_basis.copy()
    
    def damped_track_to(self, name: str, target: bpy.types.Object):
        const: bpy.types.DampedTrackConstraint = self.bone.constraints.get(name)

        if const is None:
            const = self.bone.constraints.new('DAMPED_TRACK')

        const.name = name
        const.target = target
        
        return const
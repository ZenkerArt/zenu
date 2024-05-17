from dataclasses import dataclass
from typing import TYPE_CHECKING
import bpy

if TYPE_CHECKING:
    from . import MetaBone


@dataclass
class MetaSplineData:
    control_count: int = 2


class MetaBoneData:
    List = list['MetaBoneData']
    _bone: bpy.types.Bone
    _obj: bpy.types.Object
    _arm: bpy.types.Armature

    @classmethod
    def from_pose_bone(cls, bone: bpy.types.PoseBone):
        self = cls()
        obj: bpy.types.Object = bone.id_data
        arm: bpy.types.Armature = obj.data

        self._obj = obj
        self._arm = arm

        self._bone = arm.bones[bone.name]
        return self

    @classmethod
    def from_bone(cls, bone: bpy.types.Bone, obj: bpy.types.Object):
        self = cls()
        self._pose_bone = bone
        arm: bpy.types.Armature = obj.data

        self._obj = obj
        self._arm = arm

        self._bone = arm.bones[bone.name]
        return self

    def __eq__(self, other):
        if isinstance(other, bpy.types.PoseBone):
            return self.pose_bone == other

        return super().__eq__(other)

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self._bone.name

    @property
    def arm(self):
        return self._arm

    @property
    def parent_list(self):
        return (MetaBoneData.from_pose_bone(i) for i in self.pose_bone.parent_recursive)

    @property
    def children_list(self):
        return (MetaBoneData.from_pose_bone(i) for i in self.pose_bone.children_recursive)

    @property
    def parent(self):
        if self.pose_bone.parent is None:
            return None
        return MetaBoneData.from_pose_bone(self.pose_bone.parent)

    @property
    def children(self):
        return (MetaBoneData.from_pose_bone(i) for i in self.pose_bone.children)

    @property
    def meta(self) -> 'MetaBone':
        return self._bone.zenu_meta_bone

    @property
    def props(self) -> bpy.types.bpy_struct:
        return self._bone.zenu_meta_props

    @property
    def pose_bone(self):
        return self._obj.pose.bones[self.name]

    @property
    def edit_bone(self) -> bpy.types.EditBone:
        return self._arm.edit_bones[self.name]

    @property
    def loc(self):
        return self.pose_bone.location

    @property
    def loc_tail(self):
        return self.pose_bone.location + self.pose_bone.vector

    @property
    def global_loc(self):
        arm: bpy.types.Object = self._obj
        mat = arm.matrix_world @ self.pose_bone.matrix

        return mat.translation

    @property
    def global_loc_tail(self):
        arm: bpy.types.Object = self._obj
        mat = arm.matrix_world @ self.pose_bone.matrix

        return mat.translation + self.pose_bone.vector

    def __repr__(self):
        class_name = type(self).__name__
        children_len = len(tuple(self.children))
        parent_name = ''
        if self.pose_bone.parent:
            parent_name = self.pose_bone.parent.name
        return f'<{class_name} bone_name="{self.pose_bone.name}" parent="{parent_name}" children_count={children_len}>'

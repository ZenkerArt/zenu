from dataclasses import dataclass
from typing import Literal

import bpy
from mathutils import Vector


@dataclass
class Point:
    name: str = ''
    head: Vector = Vector((0, 0, 0))
    tail: Vector = Vector((0, 0, 0))
    is_end: bool = False

    prev: 'Point' = None
    next: 'Point' = None


class RigGenerator:
    _edit_mode: str = ''
    _shapes: list[tuple[str, str]] = None
    _collections: list[tuple[str, str]] = None
    _non_selectable: list[str] = None

    def get_obj(self):
        return bpy.context.active_object

    def start_edit(self):
        obj = self.get_obj()
        self._edit_mode = obj.mode

        bpy.ops.object.mode_set(mode='EDIT')

    def end_edit(self):
        bpy.ops.object.mode_set(mode=self._edit_mode)
        self._edit_mode = ''

    def get_pose_bone(self, name: str) -> bpy.types.PoseBone:
        obj = self.get_obj()
        bone = obj.pose.bones.get(name)

        if bone is None:
            raise KeyError(f'Bone not found "{name}"')

        return bone

    def get_edit_bone(self, name: str) -> bpy.types.EditBone:
        obj = self.get_obj()
        bone = obj.data.edit_bones.get(name)

        if bone is None:
            raise KeyError(f'Bone not found "{name}"')

        return bone

    def get_bone(self, name: str) -> bpy.types.Bone:
        obj = self.get_obj()
        bone = obj.data.bones.get(name)

        if bone is None:
            raise KeyError(f'Bone not found "{name}"')

        return bone

    def create_copy_location(self, from_: str, to: str, inf: float) -> bpy.types.CopyLocationConstraint:
        obj = self.get_obj()

        bone_correction_ = self.get_pose_bone(to)

        constraint = bone_correction_.constraints.new('COPY_LOCATION')
        constraint.target = obj
        constraint.subtarget = from_
        constraint.influence = inf
        return constraint

    def create_copy_rotation(self, from_: str, to: str, inf: float) -> bpy.types.CopyRotationConstraint:
        obj = self.get_obj()

        bone_correction_ = self.get_pose_bone(to)

        constraint = bone_correction_.constraints.new('COPY_ROTATION')
        constraint.target = obj
        constraint.subtarget = from_
        constraint.influence = inf
        return constraint

    def create_copy_scale(self, from_: str, to: str, inf: float, use: tuple = None) -> bpy.types.CopyScaleConstraint:
        if use is None:
            use = ('x', 'y', 'z')
        obj = self.get_obj()

        bone_correction_ = self.get_pose_bone(to)

        constraint: bpy.types.CopyScaleConstraint = bone_correction_.constraints.new('COPY_SCALE')
        constraint.target = obj
        constraint.subtarget = from_
        constraint.influence = inf

        for coord in ('x', 'y', 'z'):
            setattr(constraint, f'use_{coord}', coord in use)
        return constraint

    def create_stretch_to(self, from_: str, to: str, inf: float) -> bpy.types.StretchToConstraint:
        obj = self.get_obj()

        bone_correction_ = self.get_pose_bone(to)

        constraint = bone_correction_.constraints.new('STRETCH_TO')
        constraint.target = obj
        constraint.subtarget = from_
        constraint.influence = inf
        return constraint

    def create_copy_transform(self, from_: str, to: str, inf: float):
        obj = self.get_obj()

        bone_correction_ = self.get_pose_bone(to)

        constraint = bone_correction_.constraints.new('COPY_TRANSFORMS')
        constraint.target = obj
        constraint.subtarget = from_
        constraint.influence = inf
        return constraint

    def create_dumped_track(self, bone: str, target: str, axis: Literal[
        "TRACK_X", "TRACK_Y", "TRACK_Z", "TRACK_NEGATIVE_X", "TRACK_NEGATIVE_Y", "TRACK_NEGATIVE_Z"]):
        obj = self.get_obj()

        bone_correction_ = self.get_pose_bone(bone)

        constraint: bpy.types.DampedTrackConstraint = bone_correction_.constraints.new('DAMPED_TRACK')
        constraint.target = obj
        constraint.subtarget = target
        constraint.track_axis = axis
        return constraint

    def create_bone(self, name: str) -> bpy.types.EditBone:
        obj = self.get_obj()
        return obj.data.edit_bones.new(name)

    def dup_bone(self, prefix: str, name: str, parent: str = None):
        obj = self.get_obj()
        edit = self._edit_mode == ''

        if edit:
            self.start_edit()

        arm: bpy.types.Armature = obj.data

        org_bone: bpy.types.EditBone = arm.edit_bones.get(name)

        bone = arm.edit_bones.new(f'{prefix}{name}')
        bone.head = org_bone.head
        bone.tail = org_bone.tail
        bone.roll = org_bone.roll

        if parent:
            bone.parent = arm.edit_bones.get(parent)

        if edit:
            self.end_edit()

        return f'{prefix}{name}'

    def duplicate_bones(self, prefix: str, bones: list[str]):
        obj = self.get_obj()

        self.start_edit()

        arm: bpy.types.Armature = obj.data

        for i in bones:
            org_bone: bpy.types.EditBone = arm.edit_bones.get(i)

            bone = arm.edit_bones.new(f'{prefix}{i}')
            bone.head = org_bone.head
            bone.tail = org_bone.tail
            bone.roll = org_bone.roll

        pbone = bones[0]
        arm.edit_bones.get(f'{prefix}{pbone}').parent = arm.edit_bones.get(pbone)

        for i in bones:
            org_bone: bpy.types.EditBone = arm.edit_bones.get(i)
            bone: bpy.types.EditBone = arm.edit_bones.get(f'{prefix}{i}')

            if org_bone.parent.name in bones:
                bone.parent = arm.edit_bones.get(f'{prefix}{org_bone.parent.name}')

        self.end_edit()

        return tuple(f'{prefix}{i}' for i in bones)

    def _get_widget(self, name: str):
        return bpy.data.objects.get(name)

    def apply_widget(self, bone_name: str, shape: str):
        if self._shapes is None:
            self._shapes = []

        self._shapes.append((bone_name, shape))

    def apply_widget_sphere(self, bone: str):
        self.apply_widget(bone, 'WGT-Sphere')

    def apply_widget_hand(self, bone: str):
        self.apply_widget(bone, 'WGT-Hand')

    def _apply_all_widgets(self):
        for bone, shape in self._shapes:
            self.get_pose_bone(bone).custom_shape = self._get_widget(shape)

        self._shapes.clear()

    def get_collection(self, name: str):
        obj = self.get_obj()
        arm: bpy.types.Armature = obj.data

        coll = arm.collections_all.get(name)
        if coll is None:
            coll = arm.collections.new(name)
        return coll

    def get_collection_all(self):
        obj = self.get_obj()
        arm: bpy.types.Armature = obj.data
        return tuple(arm.collections_all)

    def add_to_collection(self, bone: str, collection: str):
        if self._collections is None:
            self._collections = []

        paths = collection.split('/')

        first_coll = paths.pop(-1)

        prev_coll = self.get_collection(first_coll)

        for path in paths:
            new_coll = self.get_collection(path)
            prev_coll.parent = new_coll
            prev_coll = new_coll

        self._collections.append((bone, first_coll))

    def _apply_collections(self):
        obj = self.get_obj()
        if self._collections is None: return

        for bone_name, collection_path in self._collections:
            paths = collection_path.split('/')
            prev_coll = self.get_collection(paths.pop(-1))

            bone = obj.data.bones.get(bone_name)

            for c in list(bone.collections):
                c.unassign(bone)

            prev_coll.assign(bone)

        self._collections.clear()

    def parent_to_root(self, bone: str):
        self.get_edit_bone(bone).parent = self.get_edit_bone('cf_N_height')

    def set_non_selectable(self, bone: str):
        if self._non_selectable is None:
            self._non_selectable = []

        self._non_selectable.append(bone)

    def apply_all(self):
        bpy.ops.object.mode_set(mode='POSE')
        self._apply_all_widgets()

        if self._non_selectable is not None:
            for i in self._non_selectable:
                self.get_bone(i).hide_select = True

        bpy.ops.object.mode_set(mode='OBJECT')
        self._apply_collections()

        bpy.ops.object.mode_set(mode='POSE')

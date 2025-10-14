from dataclasses import field, dataclass
import math
from typing import Optional

from mathutils import Matrix, Vector
from .utils import add_empty
from .bone import OvBone
import bpy


@dataclass
class TransformFrame:
    matrix_world: Matrix
    matrix_basis: Matrix
    matrix_offset: Matrix

    matrix_result: Matrix = field(default_factory=Matrix)
    matrix_vel: Matrix = field(default_factory=Matrix)


class BoneRecord:
    _frames: dict[int, TransformFrame]
    _bone: OvBone
    _baker: 'TransformBaker'
    index: int = -1
    parent: Optional['BoneRecord'] = None
    child: Optional['BoneRecord'] = None

    def __init__(self, arm: str, bone: str, parent: 'BoneRecord'):
        self._bone = OvBone(arm, bone)
        self._frames = {}
        self.parent = parent

    @property
    def raw(self):
        return self._bone

    def add_frame(self, frame: int, transform: TransformFrame):
        self._frames[frame] = transform

    def get_frame(self, frame: int) -> TransformFrame:
        
        if frame <= self._baker.start:
            frame = self._baker.start
        
        if frame >= self._baker.end:
            frame = self._baker.end
        
        return self._frames[frame]

    def get_interpolated(self, frame: float):
        floor_frame = math.floor(frame)
        ceil_frame = math.ceil(frame)

        relative_time = frame - floor_frame

        f1 = self.get_frame(floor_frame)
        f2 = self.get_frame(ceil_frame)

        return f1.matrix_world.lerp(f2.matrix_world, relative_time), f1.matrix_offset.lerp(f2.matrix_result, relative_time)


class TransformBaker:
    _records: dict[str, BoneRecord]
    _start: int = 0
    _end: int = 0
    _offset: int = 0
    _is_bake: bool = False

    def __init__(self):
        self._records = {}

    @property
    def offset(self):
        return self._offset

    @property
    def start_offset(self):
        return self._start - self._offset

    @property
    def end_offset(self):
        return self._end + self._offset

    @property
    def start(self):
        return self.start_offset

    @property
    def end(self):
        return self._end

    @property
    def is_bake(self):
        return self._is_bake

    def add_record(self, name: str, record: BoneRecord):
        self._records[name] = record

    def add_bone(self, arm: bpy.types.Object, bone: bpy.types.PoseBone, parent: BoneRecord):
        bone_rec = BoneRecord(arm.name, bone.name, parent)
        self.add_record(bone.name, bone_rec)
        bone_rec._baker = self
        return bone_rec

    def get_by_name(self, name: str, frame: int):
        return self._records[name].get_frame(frame)

    def clear(self):
        self._records.clear()
        self._is_bake = False

    def bake(self, start: int, end: int, offset: int = 0):
        self._start = start
        self._end = end + 1

        self._offset = offset

        for frame in self.get_range_offset():
            bpy.context.scene.frame_set(frame)

            for i in self._records.values():
                _, rot, scale = i.raw.matrix.decompose()
                mat = Matrix.LocRotScale(Vector(), rot, scale)

                offset = Matrix.Translation(Vector((0, i.raw.bone.length, 0)))

                mat = i.raw.matrix_world @ offset

                i.add_frame(frame, TransformFrame(
                    matrix_world=mat,
                    matrix_basis=i.raw.matrix_basis,
                    matrix_offset=offset,
                    matrix_result=mat
                ))
        self._is_bake = True

    def get_bone_records(self):
        return list(self._records.items())

    def get_range_offset(self):
        return range(self.start_offset, self.end_offset)

    def get_range(self):
        return range(self._start, self._end)

    def get_length(self):
        return self.start - self.end


class ConstraintCreator:
    _baker: TransformBaker
    CONST_NAME = '[Zenu] Overlapper'

    def __init__(self, baker: TransformBaker):
        self._baker = baker

    def create_constraints(self):
        baker = self._baker
        bb = baker.get_bone_records()

        for i in range(len(bb)):
            _, bone_rec = bb[i]
            
            empty = add_empty(
                f'{bone_rec.raw.armature_name}_{bone_rec.raw.bone_name}'
            )
            length = bone_rec.raw.bone.length
            empty.scale = Vector((length, length, length))

            bone_rec.raw.damped_track_to(self.CONST_NAME, empty)

            for frame in baker.get_range():
                empty.matrix_world = bone_rec\
                    .get_frame(frame)\
                    .matrix_result @ Matrix.Scale(length, 4)
                empty.keyframe_insert(data_path='location', frame=frame)
                empty.keyframe_insert(data_path='rotation_euler', frame=frame)

    def remove_constraints(self):
        for bone in bpy.context.selected_pose_bones:
            empty = bpy.data.objects.get(
                f'{bpy.context.active_object.name}_{bone.name}'
            )
            const: bpy.types.DampedTrackConstraint = bone.constraints.get(
                self.CONST_NAME)

            if empty is not None:
                bpy.data.objects.remove(empty)

            if const is not None:
                bone.constraints.remove(const)

from dataclasses import field, dataclass
from typing import Optional

from mathutils import Matrix
from .bone import OvBone
import bpy


@dataclass
class TransformFrame:
    matrix_world: Matrix
    matrix_basis: Matrix

    matrix_result: Matrix = field(default_factory=Matrix)
    matrix_vel: Matrix = field(default_factory=Matrix)


class BoneRecord:
    _frames: dict[int, TransformFrame]
    _bone: OvBone
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
        return self._frames[frame]


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
                mat = Matrix.Translation(i.raw.bone.vector) @ i.raw.matrix_world
                i.add_frame(frame, TransformFrame(
                    matrix_world=mat,
                    matrix_basis=i.raw.matrix_basis,
                    matrix_result=mat
                ))
        self._is_bake = True

    def get_bone_records(self):
        return list(self._records.items())

    def get_range_offset(self):
        return range(self.start_offset, self.end_offset)

    def get_range(self):
        return range(self._start, self._end)

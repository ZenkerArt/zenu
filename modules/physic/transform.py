from typing import Optional

from mathutils import Matrix, Quaternion, Vector
import bpy


def matrix_decompose(matrix: Matrix):
    loc, rot, scale = matrix.decompose()

    return Matrix.Translation(loc), rot.to_matrix().to_4x4(), Matrix.Diagonal(scale.to_4d())


class ZTransform:
    matrix: Matrix

    def __init__(self, matrix: Matrix):
        self.matrix = matrix

    @property
    def location(self) -> Vector:
        return self.matrix.to_translation()

    @location.setter
    def location(self, value: Vector):
        loc, rot, scale = self.matrix.decompose()

        self.matrix = Matrix.LocRotScale(value, rot, scale)

    @property
    def rotation(self) -> Quaternion:
        return self.matrix.to_quaternion()

    @rotation.setter
    def rotation(self, value: Quaternion):
        loc, rot, scale = self.matrix.decompose()

        self.matrix = Matrix.LocRotScale(loc, value, scale)

    @property
    def scale(self):
        return self.matrix.to_scale()

    @scale.setter
    def scale(self, value: Vector):
        loc, rot, scale = self.matrix.decompose()

        self.matrix = Matrix.LocRotScale(loc, rot, value)


class ZTransforms:
    parent: Optional['ZTransforms'] | bpy.types.Object
    _local_transform: ZTransform
    _delta_transform: ZTransform
    motion: ZTransform

    def __init__(self):
        self.offset = Vector()
        self.parent = None
        self._local_transform = ZTransform(Matrix())
        self._delta_transform = ZTransform(Matrix())
        self.motion = ZTransform(Matrix())

    @property
    def matrix_local(self):
        return self._local_transform.matrix

    @matrix_local.setter
    def matrix_local(self, value: Matrix):
        self._local_transform.matrix = value

    @property
    def matrix_delta(self):
        return self._delta_transform.matrix

    @matrix_delta.setter
    def matrix_delta(self, value: Matrix):
        self._delta_transform.matrix = value

    @property
    def matrix_world(self):
        mat = getattr(self.parent, 'matrix_world', None)
        if mat is None:
            mat = Matrix()
        return mat @ self.matrix_local

    @property
    def matrix_world_delta(self):
        mat = getattr(self.parent, 'matrix_world_delta', None) or getattr(self.parent, 'matrix_world', None)
        if mat is None:
            mat = Matrix()
        return mat @ self.matrix_local @ self.matrix_delta @ self.motion.matrix

    @property
    def local(self):
        return self._local_transform

    @property
    def delta(self):
        return self._delta_transform

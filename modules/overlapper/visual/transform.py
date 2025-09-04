from typing import Optional

from mathutils import Matrix, Quaternion, Vector
import bpy


class ZTransform:
    matrix: Matrix

    def __init__(self, matrix: Matrix):
        self.matrix = matrix

    @property
    def location(self) -> Vector:
        return self.matrix.to_translation()

    @location.setter
    def location(self, value: Vector):
        _, rot, scale = self.matrix.decompose()

        self.matrix = Matrix.LocRotScale(value, rot, scale)

    @property
    def rotation(self) -> Quaternion:
        return self.matrix.to_quaternion()

    @rotation.setter
    def rotation(self, value: Quaternion):
        loc, _, scale = self.matrix.decompose()

        self.matrix = Matrix.LocRotScale(loc, value, scale)

    @property
    def scale(self):
        return self.matrix.to_scale()

    @scale.setter
    def scale(self, value: Vector):
        loc, rot, _ = self.matrix.decompose()

        self.matrix = Matrix.LocRotScale(loc, rot, value)


class ZTransforms:
    parent: Optional['ZTransforms'] | bpy.types.Object
    _local_transform: ZTransform

    def __init__(self):
        self.offset = Vector()
        self.parent = None
        self._local_transform = ZTransform(Matrix())

    @property
    def matrix_local(self):
        return self._local_transform.matrix

    @property
    def matrix_world(self):
        mat = getattr(self.parent, 'matrix_world', None)
        if mat is None:
            mat = Matrix()

        return mat @ self.matrix_local

    @property
    def local(self):
        return self._local_transform

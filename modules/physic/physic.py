import math
from typing import Union, Iterator

import bpy
from mathutils import Vector, Quaternion, Matrix


def add_empty(name: str):
    empty = bpy.data.objects.get(name)

    if empty:
        return empty

    empty = bpy.data.objects.new(name, None)
    bpy.context.view_layer.layer_collection.collection.objects.link(empty)

    return empty


class ZTime:
    delta: float
    elapsed: float = 0

    def __init__(self):
        self.delta = 1 / 60

    def update(self):
        self.elapsed += self.delta


class ZTransforms:
    offset: Vector
    rotation_quat: Quaternion
    location_mat: Matrix

    def __init__(self):
        self.offset = Vector()
        self.rotation_quat = Quaternion()
        self.location_mat = Matrix()

    @property
    def matrix(self) -> Matrix:
        offset = Matrix.Translation(self.offset)
        return self.location_mat @ self.rotation_quat.to_matrix().to_4x4() @ offset

    @property
    def location(self):
        return self.matrix.to_translation()

    @property
    def rotation(self):
        return self.matrix.to_quaternion()

    @rotation.setter
    def rotation(self, value: Quaternion):
        self.rotation_quat = value

    def parent_to(self, transforms: Union['ZTransforms', Matrix]):
        if isinstance(transforms, ZTransforms):
            self.parent_to(transforms.matrix)
        elif isinstance(transforms, Matrix):
            translation = transforms.to_translation()
            quat = transforms.to_quaternion()

            self.location_mat = Matrix.Translation(translation)
            self.rotation_quat = quat


class ZConstraint:
    parent: 'ZConstraint' = None
    child: 'ZConstraint' = None
    transforms: ZTransforms
    transforms_physic: ZTransforms
    target_object: bpy.types.Object

    def __init__(self, obj: bpy.types.Object):
        self.transforms = ZTransforms()
        self.transforms_physic = ZTransforms()
        self.target_object = obj

    @property
    def matrix(self):
        return self.transforms.matrix


class ZConstraints:
    _constraints: list[ZConstraint]

    def __init__(self):
        self._constraints = []

    def __iter__(self) -> Iterator[ZConstraint]:
        return self._constraints.__iter__()

    def __getitem__(self, item: int) -> ZConstraint:
        return self._constraints[item]

    @property
    def raw(self):
        return self._constraints

    def add(self, const: ZConstraint):
        self._constraints.append(const)


class ZContext:
    time: ZTime
    constraints: ZConstraints

    def __init__(self):
        self.time = ZTime()
        self.constraints = ZConstraints()


zn_context = ZContext()


def loop():
    first_constraint = zn_context.constraints[0]
    first_obj = first_constraint.target_object
    first_constraint.transforms.parent_to(first_obj.matrix_world)

    for index, const in enumerate(zn_context.constraints):
        if const.parent is None:
            continue


        const.target_object.matrix_world = const.transforms.matrix

        const.transforms.parent_to(const.parent.transforms)

        # const.transforms_physic.location_mat = const.transforms.location_mat
        # const.transforms_physic.offset = const.transforms.offset

        # const.transforms_physic.rotation = const.transforms_physic.rotation.slerp(const.transforms.rotation, zn_context.time.delta)
        # const.transforms_physic.parent_to(const.transforms)
        if index == 1:
            vec = const.parent.transforms.matrix.to_quaternion().inverted() @ Vector((1, 0, 0))
            const.transforms.rotation = const.transforms.rotation @ Quaternion(vec, math.pi / 2)
        # print(const.transforms_physic.rotation)


    zn_context.time.update()


def init():
    zn_context.time.delta = 1 / bpy.context.scene.render.fps
    offset = Vector((0, 0, 2))
    zn_context.constraints.raw.clear()
    parent = None
    for i in range(2):
        const = ZConstraint(add_empty(f'Const_{i}' ))
        const.target_object.location = offset * i
        const.parent = parent
        if i > 0:
            const.transforms.offset = offset

        if parent is not None:
            parent.child = const

        parent = const

        zn_context.constraints.add(const)

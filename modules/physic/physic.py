import bpy
from mathutils import Vector, Quaternion, Matrix


def add_empty(name: str):
    empty = bpy.data.objects.get(name)

    if empty:
        return empty

    empty = bpy.data.objects.new(name, None)
    bpy.context.view_layer.layer_collection.collection.objects.link(empty)

    return empty


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
        return (self.location_mat @ self.rotation_quat.to_matrix().to_4x4()) @ offset

    @property
    def location(self):
        return self.matrix.to_translation()

    @property
    def rotation(self):
        return self.matrix.to_quaternion()


class ZConstraint:
    parent: 'ZConstraint' = None
    child: 'ZConstraint' = None
    point: ZTransforms
    target_object: bpy.types.Object

    def __init__(self, obj: bpy.types.Object):
        self.point = ZTransforms()
        self.target_object = obj

    @property
    def matrix(self):
        return self.point.matrix


class ZConstraints:
    _constraints: list[ZConstraint]

    def __init__(self):
        self._constraints = []

    @property
    def constraints(self):
        return self._constraints

    def add(self, const: ZConstraint):
        self._constraints.append(const)


z_constraints = ZConstraints()


def loop():
    first_constraint = z_constraints.constraints[0]
    first_obj = first_constraint.target_object

    translation = first_obj.matrix_world.to_translation()
    quat = first_obj.matrix_world.to_quaternion()

    # print(quat)

    first_constraint.point.location_mat = Matrix.Translation(translation)
    first_constraint.point.rotation_quat = quat

    for const in z_constraints.constraints:
        if const.parent is None:
            continue

        const.point.location_mat = const.parent.point.location_mat.copy()
        const.point.rotation_quat = const.parent.point.rotation_quat.copy()

        const.target_object.matrix_world = const.matrix


def init():
    offset = Vector((0, 0, 1))

    parent = None
    for i in range(10):
        off = offset * i

        const = ZConstraint(add_empty(f'Const_{i}'))
        const.target_object.location = off.copy()
        const.parent = parent
        const.point.offset = off.copy()

        if parent is not None:
            parent.child = const

        parent = const

        z_constraints.add(const)

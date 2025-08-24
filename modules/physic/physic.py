import json
import math
from typing import Iterator

import bpy
from mathutils import Vector, Quaternion, Matrix
from .settings import get_physic_settings
from .transform import ZTransforms
from .visual import ZVisualizer


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


class ZBone:
    _bone: str
    _arm: str
    _constraints: list[str]

    def __init__(self, bone: bpy.types.PoseBone, arm: bpy.types.Object):
        self._bone = bone.name
        self._arm = arm.name
        self._constraints = []

    @property
    def arm(self) -> bpy.types.Object:
        return bpy.data.objects[self._arm]

    @property
    def bone(self) -> bpy.types.PoseBone:
        return self.arm.pose.bones[self._bone]

    @property
    def matrix_world(self):
        return self.arm.matrix_world @ self.bone.matrix

    @property
    def matrix(self):
        return self.bone.matrix

    @property
    def location(self):
        return self.matrix_world.to_translation()

    @property
    def location_tail(self):
        return self.matrix_world.to_translation() + self.bone.vector

    @property
    def rotation(self):
        return self.matrix_world.to_quaternion()

    def destroy(self):
        for i in self._constraints:
            const = self.bone.constraints.get(i)

            if const:
                self.bone.constraints.remove(const)

    def child_of(self, obj: bpy.types.Object):
        const = obj.constraints.get('[ZENU]Physic')
        if const is not None:
            obj.constraints.remove(const)
        const: bpy.types.ChildOfConstraint = obj.constraints.new('CHILD_OF')
        const.name = '[ZENU]Physic'
        const.target = self.arm
        const.subtarget = self.bone.name
        const.inverse_matrix = self.matrix_world.inverted()

    def damped_track(self, obj: bpy.types.Object):
        const = self.bone.constraints.get('[ZENU]Physic')
        if const is not None:
            self.bone.constraints.remove(const)

        const = self.bone.constraints.new('DAMPED_TRACK')
        const.name = '[ZENU]Physic'

        const.target = obj
        self._constraints.append(const.name)


class ZConstraint:
    _target_object: str

    parent: 'ZConstraint' = None
    child: 'ZConstraint' = None
    transforms: ZTransforms
    target_bone: ZBone
    root_bone: ZBone
    angular_velocity: Vector
    rotation: Quaternion
    location_velocity: Vector
    rest_matrix: Matrix

    def __init__(self, obj: bpy.types.Object, target_bone: ZBone):
        self.transforms = ZTransforms()
        self.transforms_delta = ZTransforms()
        self._target_object = obj.name
        self.target_bone = target_bone
        self.angular_velocity = Vector()
        self.rotation = Quaternion()
        self.location_velocity = Vector()
        self.rest_matrix = Matrix()

    @property
    def target_object(self):
        return bpy.data.objects.get(self._target_object)

    @property
    def matrix(self):
        return self.transforms.matrix

    def destroy(self):
        if self.target_object is None:
            self.target_bone.destroy()
            return

        try:
            bpy.data.objects.remove(self.target_object)
        except ReferenceError:
            pass
        self.target_bone.destroy()


class ZConstraints:
    _constraints: list[ZConstraint]
    _empty: str = ''
    angular_solver: 'ZAngularSolver'

    def __init__(self):
        self._constraints = []
        self.angular_solver = ZAngularSolver()

    def __iter__(self) -> Iterator[ZConstraint]:
        return self._constraints.__iter__()

    def __getitem__(self, item: int) -> ZConstraint:
        return self._constraints[item]

    @property
    def empty(self):
        return bpy.data.objects.get(self._empty)

    @empty.setter
    def empty(self, value: bpy.types.Object):
        self._empty = value.name

    @property
    def raw(self):
        return self._constraints

    def add(self, const: ZConstraint):
        self._constraints.append(const)

    def destroy(self):
        for i in self._constraints:
            i.destroy()

        self._constraints.clear()

        if self.empty:
            bpy.data.objects.remove(self.empty)


class ZAngularSolverSettings:
    stiffness: float = 100
    damping: float = 10


class ZAngularSolver:
    settings: ZAngularSolverSettings
    delta_time: float = 1 / 60

    def __init__(self):
        self.settings = ZAngularSolverSettings()

    def solve(self, q_current: Quaternion, q_target: Quaternion, angular_velocity: Vector):
        stiffness, damping, dt = self.settings.stiffness, self.settings.damping, self.delta_time

        if q_current.dot(q_target) < 0.0:
            q_target = -q_target

        q_delta = q_target @ q_current.conjugated()
        angle = q_delta.angle
        axis = q_delta.axis
        angular_velocity += axis * angle * stiffness * dt
        angular_velocity *= math.exp(-damping * dt)

        speed = angular_velocity.length

        if speed > 1e-8:
            axis_norm = angular_velocity / speed
            q_step = Quaternion(axis_norm, speed * dt)
            q_current = q_step @ q_current

        return q_current, angular_velocity


class ZContext:
    time: ZTime
    constraints: list[ZConstraints]
    visual: ZVisualizer

    def __init__(self):
        self.time = ZTime()
        self.constraints = []
        self.visual = ZVisualizer()


zn_context = ZContext()


def loop():
    for c in zn_context.constraints:
        count = len(c.raw)
        first_constraint = c[0]
        vis1 = zn_context.visual.get_xyz_point(c.empty.name)

        first_constraint.location_velocity += ((
                                                       first_constraint.root_bone.matrix_world @ first_constraint.rest_matrix).to_translation() - first_constraint.location_velocity) * .1

        vis1.transforms.local.location = first_constraint.location_velocity
        c.empty.location = first_constraint.location_velocity

        for index, const in enumerate(c):
            if const.parent is None:
                continue

            target_rot = const.parent.transforms.matrix_world_delta.to_quaternion()

            const.rotation, const.angular_velocity = c.angular_solver.solve(const.rotation.copy(), target_rot,
                                                                            const.angular_velocity.copy())

            mat = const.parent.transforms.matrix_world_delta.to_quaternion().inverted()
            const.transforms.delta.rotation = mat @ const.rotation

            const.target_object.matrix_world = const.transforms.matrix_world_delta @ Matrix.Scale(
                const.target_bone.bone.length,
                4)

    zn_context.time.update()


def test_empties():
    zn_context.time.delta = 1 / bpy.context.scene.render.fps
    offset = Vector((0, 0, 2))
    constraints = ZConstraints()

    zn_context.constraints.clear()
    zn_context.constraints.append(constraints)
    parent = None
    for i in range(10):
        const = ZConstraint(add_empty(f'Bone_{i}'), None)
        const.target_object.matrix_world = Matrix()
        const.target_object.location = offset * i
        const.parent = parent

        if i == 0:
            const.transforms.parent = const.target_object
        else:
            const.transforms.parent = parent.transforms
            const.transforms.local.location = Vector((0, 0, 2))

            parent.child = const

        parent = const

        constraints.add(const)


def find_bone_chain(bone: bpy.types.PoseBone, bones: list[bpy.types.PoseBone] = None):
    if bone.child is None:
        bones.append(bone)
        return bones

    if bones is None:
        bones = []

    child_pos = bone.child.matrix.to_translation()
    pos = bone.matrix.to_translation() + bone.vector

    length = abs((child_pos - pos).length)

    if length < .01:
        bones.append(bone)
        return find_bone_chain(bone.child, bones)

    return bones


def add_bone_chain(arm: bpy.types.Object, bones: list[bpy.types.PoseBone]):
    parent = None
    constraints = ZConstraints()

    for i, bone in enumerate(bones):
        bone = ZBone(bone, arm)

        const = ZConstraint(add_empty(f'{arm.name}_{bone.bone.name}'), bone)
        const.parent = parent
        const.target_object.location = bone.location_tail
        if bone.bone.parent is not None:
            const.rest_matrix = bone.bone.parent.matrix.inverted() @ Matrix.Translation(
                bone.bone.vector * 2) @ bone.matrix

        if i == 0:
            constraints.empty = add_empty(f'Target_{bone.bone.parent.name}_{bone.bone.name}')
            const.transforms.parent = const.target_object
            bone.child_of(const.target_object)
            bone.damped_track(constraints.empty)
            const.root_bone = ZBone(bone.bone.parent, arm)
        else:
            const.transforms.parent = parent.transforms
            const.transforms.local.location = bone.location_tail - parent.target_bone.location_tail
            bone.damped_track(const.target_object)
            parent.child = const

        parent = const
        constraints.add(const)

    return constraints


def add_on_selected_bone():
    context = bpy.context
    arm = context.active_object
    settings = get_physic_settings()

    if settings.auto_sort:
        for bbone in context.selected_pose_bones:
            constraints = add_bone_chain(arm, find_bone_chain(bbone))
            zn_context.constraints.append(constraints)
    else:
        for coll in context.scene.zenu_physic_chain_collection:
            bones = [coll.obj.pose.bones[i] for i in json.loads(coll.constraints).keys()]
            # print(bones)
            constraints = add_bone_chain(coll.obj, bones)
            constraints.angular_solver.settings = coll

            zn_context.constraints.append(constraints)


def init():
    add_on_selected_bone()
    # test_empties()


def clear():
    for i in zn_context.constraints:
        i.destroy()
    zn_context.constraints.clear()
    zn_context.visual.clear()


def reg():
    zn_context.visual.register()


def unreg():
    zn_context.visual.unregister()

import math
from dataclasses import dataclass
from typing import Optional

import bpy
from bpy.app.handlers import persistent
from bpy.types import Context
from mathutils import Vector, Matrix, Quaternion, Euler
from .physic import loop, init
from ...base_panel import BasePanel


@dataclass
class QAngularDataBlock:
    angular_velocity: Vector = Vector()
    rotation: Quaternion = Quaternion()
    rotation_vel: Quaternion = Quaternion()


class QAngularSolverSettings:
    stiffness: float = 100
    damping: float = 10


def lock_quaternion_axes(quat: Quaternion, lock_axes=("X",)):
    """
    Убирает вращение вокруг указанных осей из кватерниона.

    :param quat: mathutils.Quaternion
    :param lock_axes: tuple/list из 'X', 'Y', 'Z'
    :return: новый mathutils.Quaternion
    """
    # Кватернион -> матрица вращения
    rot_matrix = quat.to_matrix()

    # Берём forward (ось Z) и up (ось Y) векторы
    forward = rot_matrix.col[2].copy()
    up = rot_matrix.col[1].copy()

    # Обнуляем компоненты для заблокированных осей
    for axis in lock_axes:
        idx = {"X": 0, "Y": 1, "Z": 2}[axis.upper()]
        forward[idx] = 0.0
        up[idx] = 0.0

    # Нормализация направлений
    forward.normalize()
    up.normalize()

    # Правый вектор (ось X) = cross(up, forward)
    right = up.cross(forward)
    right.normalize()

    # Пересобираем up, чтобы была ортогональность
    up = forward.cross(right)

    # Собираем матрицу вращения
    new_rot_matrix = Matrix((right, up, forward)).transposed()

    # Матрица -> кватернион
    return new_rot_matrix.to_quaternion()

class QAngularSolver:
    settings: QAngularSolverSettings
    delta_time: float = 1 / 60

    def __init__(self):
        self.settings = QAngularSolverSettings()

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

    def solve_block(self, block: QAngularDataBlock):
        block.rotation_vel, block.angular_velocity = self.solve(block.rotation_vel.copy(), block.rotation,
                                                                block.angular_velocity.copy())


class ChainNode:
    parent: Optional['ChainNode']
    angular_block: QAngularDataBlock
    bone: bpy.types.PoseBone
    motion_vector: Vector
    prev_position: Vector
    matrix: Matrix
    obj: bpy.types.Object
    offset: Vector
    index: int = -1

    def __init__(self, empty: bpy.types.Object):
        self.obj = empty
        self.matrix = Matrix.Translation(Vector((0, 0, 0)))
        self.angular_block = QAngularDataBlock()
        self.motion_vector = Vector()
        self.prev_position = Vector()

    @property
    def rotation(self):
        return self.angular_block.rotation_vel

    @rotation.setter
    def rotation(self, value: Quaternion):
        self.angular_block.rotation = value

    @property
    def position(self):
        return self.obj.matrix_world.translation

    @property
    def obj_rotation(self) -> Quaternion:
        return self.bone.matrix.to_quaternion()

    @property
    def bone_position(self):
        return self.bone.matrix.to_translation()

    @position.setter
    def position(self, value: Vector):
        self.obj.location = value


class RootNode:
    _chains: list[ChainNode]
    _bones: list[bpy.types.PoseBone]
    _angular_solver: QAngularSolver
    _debug_empty: bpy.types.Object

    def __init__(self):
        self._chains = list()
        self._bones = list()
        self._angular_solver = QAngularSolver()
        self._angular_solver.delta_time = 1 / bpy.context.scene.render.fps
        self._angular_solver.settings = bpy.context.scene.zenu_physic_settings
        self._debug_empty = self.add_empty(bpy.context, 'DebugEmpty')

    @staticmethod
    def add_empty(context: bpy.types.Context, name: str):
        empty = bpy.data.objects.get(name)

        if empty:
            return empty

        empty = bpy.data.objects.new(name, None)
        context.view_layer.layer_collection.collection.objects.link(empty)

        return empty

    def set_bones(self, arm: bpy.types.Object, bones: list[bpy.types.PoseBone]):
        self._chains.clear()
        self._bones.clear()

        context = bpy.context
        parent = None

        for index, bone in enumerate(bones):
            empty = self.add_empty(context, bone.name)
            chain_node = ChainNode(empty)
            chain_node.bone = bone

            mat = arm.matrix_world @ bone.matrix
            loc = mat.translation + bone.vector

            empty.location = loc
            empty.scale = (.1, .1, .1)

            chain_node.parent = parent
            chain_node.index = index + 1

            if parent is None:
                const = empty.constraints.get('[ZENU]Physic')
                if const is not None:
                    empty.constraints.remove(const)
                const: bpy.types.ChildOfConstraint = empty.constraints.new('CHILD_OF')
                const.name = '[ZENU]Physic'
                const.target = arm
                const.subtarget = bone.name
                const.inverse_matrix = (arm.matrix_world @ bone.matrix).inverted()
                # const.inverse_matrix

            if parent is not None:
                chain_node.offset = loc - parent.position

                const = bone.constraints.get('[ZENU]Physic')
                if const is not None:
                    bone.constraints.remove(const)

                const = bone.constraints.new('DAMPED_TRACK')
                const.name = '[ZENU]Physic'

                const.target = empty

            parent = chain_node
            self._bones.append(bone)
            self._chains.append(chain_node)
        # arm.data.pose_position = 'POSE'

    def solve(self):
        ob = self._chains[0]

        ob.matrix = ob.obj.matrix_world

        rota = ob.angular_block.rotation
        # rot = lock_quaternion_axes(quat=rot, lock_axes=("y",))

        quat = quaternion_to_matrix(rota)

        count = len(self._chains)

        motion_vector = rota @ (ob.prev_position - ob.bone_position)

        v1 = ob.bone_position  # начальное направление
        v2 = self._debug_empty.location  # целевое направление


        for i in self._chains:

            if i.parent is None:
                continue

            m = motion_vector * 20 * (1 - i.index / count)

            obj_pos, obj_rot = get_matrix_rot_pos(i.parent.matrix)
            mat = i.matrix.to_3x3().inverted()
            vec_local = mat @ Vector((0, 1, 0))  # мировая Y в локальных координатах
            vec_local.normalize()
            i.angular_block.angular_velocity += vec_local

                # self._debug_empty.matrix_world = i.matrix.inverted()

            rot = obj_rot.to_quaternion()
            self._angular_solver.solve_block(i.angular_block)

            i.rotation = rot
            trans = Matrix.Translation(i.offset)



            i.matrix = (obj_pos @ quaternion_to_matrix(i.rotation)) @ trans
            i.position = i.matrix.to_translation()

        ob.prev_position = ob.bone_position.copy()


root_node = None


def quaternion_to_matrix(mat: Quaternion):
    angle_vector, value = mat.to_axis_angle()
    return Matrix.Rotation(value, 4, angle_vector)


def get_matrix_rot_pos(mat: Matrix):
    obj_pos = Matrix.Translation(mat.to_translation())
    obj_rot = quaternion_to_matrix(mat.to_quaternion())

    return obj_pos, obj_rot


@persistent
def load_handler(dummy):
    loop()
    # if root_node:
    #     root_node.solve()


class ZENU_OT_add_bone(bpy.types.Operator):
    bl_label = 'Add Bone'
    bl_idname = 'zenu.add_bone'

    def add_empty(self, context: bpy.types.Context, name: str):
        empty = bpy.data.objects.new(name, None)
        context.view_layer.layer_collection.collection.objects.link(empty)
        return empty

    def execute(self, context: bpy.types.Context):
        init()
        # global root_node
        # arm = context.active_object
        # # arm.data.pose_position = 'REST'
        # root_node = RootNode()
        #
        # bones = list()
        #
        # bones.append(context.active_pose_bone)
        # bones.extend(context.active_pose_bone.children_recursive)
        #
        # root_node.set_bones(arm, bones)
        # arm.data.pose_position = 'POSE'
        return {'FINISHED'}


class ZENU_PT_phyisc(BasePanel):
    bl_label = 'Physic'
    bl_context = ''

    def draw(self, context: Context):
        layout = self.layout
        layout.operator(ZENU_OT_add_bone.bl_idname)

        settings: QAngularSolverSettings = context.scene.zenu_physic_settings

        col = layout.column(align=True)
        col.prop(settings, 'stiffness')
        col.prop(settings, 'damping')


class QAngularSettings(bpy.types.PropertyGroup):
    stiffness: bpy.props.FloatProperty(default=100)
    damping: bpy.props.FloatProperty(default=10)
    # delta_time: float = 1 / 60


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_phyisc,
    ZENU_OT_add_bone,
    QAngularSettings
))


def register():
    bpy.types.Scene.zenu_float_curve = bpy.props.FloatProperty()
    bpy.app.handlers.frame_change_post.append(load_handler)
    reg()

    bpy.types.Scene.zenu_physic_settings = bpy.props.PointerProperty(type=QAngularSettings)



def unregister():
    bpy.app.handlers.frame_change_post.remove(load_handler)
    unreg()

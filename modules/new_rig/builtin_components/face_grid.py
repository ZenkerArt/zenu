from collections import Counter
from dataclasses import dataclass, field
from logging import root
from typing import Any, Type
import bpy
from mathutils import Vector
from ..layers import BoneCollectorLayer, CopyConstraintLayer, StyleLayer, BoneCollectionLayer
from ..rig_lib import RigComponent, RigContext, RigBone
from ..rig_lib.bone_utils import bone_get_head, bone_create_lerp, clear_bone_collection, bone_get_side


@dataclass
class Point:
    loc: Vector
    name: str
    bone: RigBone = None
    parent_to: RigBone = None
    
    bones: set[str] = field(default_factory=set)


class Points:
    _points: list[Point]
    _arm: bpy.types.Object

    def __init__(self, arm: bpy.types.Object):
        self._points = []
        self._arm = arm

    @property
    def points(self):
        return self._points

    def add_point(self, vec: Vector, name: str):
        p = self.get_point(vec)

        if p:
            p.bones.add(name)
            return p

        p = Point(
            name=name,
            loc=vec.copy(),
            bones={name,}
        )

        self._points.append(p)

        return p

    def get_point(self, vec: Vector):
        for p in self._points:
            if abs((p.loc - vec).length) < .001:
                return p

        return None

    def get_near_bone(self, vec: Vector):
        length = 100
        point = None

        for p in self._points:
            ll = abs((p.loc - vec).length)
            if ll < length:
                length = ll
                point = p

        return point

    # def
    
    def create_bones(self):
        for point in self._points:
            if len(point.bones) > 1:
                sp = point.name.split('.')
                side_ = sp[0]
                name = sp[1]
                
                point.name = f'T-{side_}.{name}'
            # print()

        for point in self._points:
            if point.bone is not None:
                continue

            b = self._arm.data.edit_bones.new(f'CTR-{point.name}')
            b.use_deform = False
            b.use_connect = False

            b.head = point.loc
            b.tail = point.loc + Vector((0, 0, .005))
            b.bbone_x = 0.001
            b.bbone_z = 0.001

            try:
                if point.parent_to:
                    b.parent = point.parent_to.edit
            except TypeError:
                pass

            point.bone = RigBone(self._arm, b)


class BoneGroup:
    _root_bone: RigBone
    _mid_bones: list[RigBone]
    _points: Points
    local_points: list[Point]

    def __init__(self, root_bone: RigBone, points: Points = None):
        self._points = points or Points(root_bone.arm)

        self._root_bone = root_bone
        self._mid_bones = []
        self.local_points = []

        self._mid_bones.append(self._root_bone)
        self._mid_bones.extend(
            list(RigBone(root_bone.arm, i)
                 for i in self._root_bone.edit.children_recursive if i.name)
        )

        self._root_bone.edit.color.palette = 'THEME03'

        for i in self._mid_bones:
            i.edit.color.palette = 'THEME14'
            p = self._points.add_point(i.edit.head, i.name)
            p.parent_to = RigBone(self._root_bone.arm,
                                  self._root_bone.edit.parent)
            self.local_points.append(p)

        i = self._mid_bones[-1]
        p = self._points.add_point(i.edit.tail, i.name)
        p.parent_to = RigBone(self._root_bone.arm, self._root_bone.edit.parent)
        self.local_points.append(p)
        # self._points.create_bones(self._root_bone.arm)

    @property
    def bones(self):
        return self._mid_bones

    def parent_all(self):
        for i in self._mid_bones:
            point = self._points.get_point(i.edit.head)

            i.edit.use_connect = False
            i.edit.parent = point.bone.edit

    def pose_parent(self):
        for i in self._mid_bones:
            pose_bone = i.pose

            point = self._points.get_near_bone(pose_bone.tail)

            stretch_to: bpy.types.StretchToConstraint = pose_bone.constraints.new(
                'STRETCH_TO')

            stretch_to.target = self._root_bone.arm
            stretch_to.subtarget = point.bone.name


class FaceGrid(RigComponent):
    name = 'Face Grid'

    points: Points
    tail: list[str]
    bone_groups: list[BoneGroup]

    def __init__(self):
        super().__init__()

        self.points = None
        self.tail = []
        self.bone_groups = []

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        pass

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, style: StyleLayer, coll_ls: BoneCollectionLayer):
        arm_obj = context.new_armature
        arm = context.new_arm
        bones = bones_collector.get_edit_bones_by_type(self)
        points = Points(arm_obj)
        self.points = points

        for bone in bones:
            rb = RigBone(arm_obj, bone.name)
            self.bone_groups.append(BoneGroup(rb, points))

        points.create_bones()

        for bone in self.bone_groups:
            bone.parent_all()
            coll = bone._root_bone.edit.collections[0]

            for p in bone.local_points:
                st_coll = coll_ls.get_collection(f'{coll.name} Stretch')
                st_coll.parent = coll

                style.apply_shape(p.bone, bone._root_bone.props.shape)
                clear_bone_collection(p.bone.edit)
                st_coll.assign(p.bone.edit)

        for bone in self.bone_groups:
            for b in bone.bones:
                coll_ls.add_to_deform(b)

    def execute_pose(self, context: RigContext, bones_collector: BoneCollectorLayer):
        for i in self.bone_groups:
            i.pose_parent()

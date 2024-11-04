from dataclasses import dataclass

import bpy
from bpy.app.handlers import persistent
from mathutils import Vector
from ....curve import Beizer, CurveDraw
from ..rig_module import RigModule
from ...meta_bone import MetaBoneData
from rna_prop_ui import rna_idprop_ui_create
from zenu_library import BezierCurve, BezierPoint

from ...bone_utils import bone_copy_transforms, bone_get_side, bone_clone, bone_connect, bone_disable_deform, \
    bone_get_head
from ...shapes import ShapesEnum
from ....visualization import visualization

curve_bones_control: tuple[tuple[str, str, str]] = tuple()
curve_bones: list[tuple[str, str, str]] = []
curve_arm: str
b = CurveDraw()


@dataclass
class SplineBind:
    fit: str
    original: str
    deform: str


@dataclass()
class CopyRotation:
    bone: str
    targets: list[str]
    # inf: float = 1


# @persistent
# def update(context):
#     b.clear()
#     target = bpy.data.objects['Empty']
#     visualization.clear()
#
#     cur = None
#     index = 0
#
#     arm = bpy.data.objects[curve_arm]
#
#     #
#     for center, left, right in curve_bones_control:
#         center_bone = arm.pose.bones[center]
#         center = bone_get_head(arm.pose.bones[center])
#         left = bone_get_head(arm.pose.bones[left])
#         right = bone_get_head(arm.pose.bones[right])
#
#         if cur:
#             c, l, r = cur
#             b.add(Beizer(
#                 p0=center,
#                 p1=left,
#                 p2=r,
#                 p3=c,
#                 attributes={'angle': center_bone['zenu_angle']}
#             ))
#
#         cur = (center, left, right)
#
#         if index > len(curve_bones_control) - 2:
#             continue
#
#         index += 1
#
#     b.rebuild()
#     for center in curve_bones:
#         center_bone = MetaBoneData.from_pose_bone(arm.pose.bones[center])
#     #
#         point = b.get_closer_point_lerp(center_bone.global_loc)
#         center_bone.pose_bone.rotation_quaternion.y = point.attributes['angle']
#
#         # visualization.add_point(point.pos, color=(abs(point.attributes['angle']), 0, 0))


class SplineIKRig(RigModule):
    rig_name = 'Spline IK Advanced'

    auto_detect: bpy.props.BoolProperty(name='Auto Detect', default=True)
    chain_length: bpy.props.IntProperty(name='Chain Length', min=2, default=2, soft_max=100, subtype='FACTOR')

    spline_point_count: bpy.props.IntProperty(name='Point Count', min=2, default=3, soft_max=10, subtype='FACTOR')
    root_bone: bpy.props.StringProperty(name='Root Bone')

    _indexs: list[tuple[bpy.types.Object, str, int]]
    _spline_fit_constraint_bone: str = ''
    _spline_original_constraint_bone: str = ''
    _bones_parent: list[SplineBind]
    _copy_rotation: list[CopyRotation]

    def init(self):
        self._indexs = []
        self._bones_parent = []
        self._copy_rotation = []

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        props = self.props

        box = layout.box().column(align=True)
        box.label(text='Spline')
        box.prop(props, self.get_prop_name('spline_point_count'))

        box = layout.box().column(align=True)
        box.label(text='Chain Length')
        box.prop(props, self.get_prop_name('auto_detect'))
        if not self.auto_detect:
            box.prop(props, self.get_prop_name('chain_length'))

        col = layout.column(align=True)
        col.label(text='Root Bone')
        col.prop_search(props, self.get_prop_name('root_bone'), self.bone.arm, 'bones', text='')

    def register(self) -> tuple:
        # bpy.app.handlers.frame_change_post.append(update)
        return tuple()

    def unregister(self) -> tuple:
        # bpy.app.handlers.frame_change_post.remove(update)
        return tuple()

    def get_bones(self, bone: MetaBoneData):
        yield self.bone
        for index, bone in enumerate(bone.parent_list):
            if bone.parent is None:
                yield bone
                break

            if not self.auto_detect:
                if index > self.chain_length - 3:
                    yield bone
                    break
                continue

            if (bone.global_loc - bone.parent.global_loc_tail).length > .01:
                yield bone
                break
            yield bone
        # yield self.bone

    def generate_spline(self, bones: list[MetaBoneData], point_count: int) -> tuple[
        list[tuple[Vector, Vector, Vector]], bpy.types.Object]:
        point_list = []

        start_bone = bones[-1]
        end_bone = bones[0]

        curve_data = bpy.data.curves.new('SplineRigData', type='CURVE')
        curve_obj = bpy.data.objects.new('SplineRig', curve_data)
        bpy.context.scene.collection.objects.link(curve_obj)

        curve_data.dimensions = '3D'
        spline = curve_data.splines.new('BEZIER')

        spline.bezier_points.add(point_count - 1)
        points_count = len(spline.bezier_points) - 1

        diff = (start_bone.global_loc - end_bone.global_loc_tail)
        direction = diff.normalized()
        distance = diff.length

        for index, point in enumerate(spline.bezier_points):
            pos = start_bone.global_loc.lerp(end_bone.global_loc_tail, index / points_count)
            offset = (direction * (distance / points_count)) * .3

            point.co = pos
            point.handle_left = pos + offset
            point.handle_right = pos - offset

            point_list.append((point.co, point.handle_left, point.handle_right))

        self.add_dep(curve_obj)
        return point_list, curve_obj

    def create_controls(self, bones: list[MetaBoneData], points: list[tuple[Vector, Vector, Vector]],
                        curve_obj: bpy.types.Object) -> list[bpy.types.EditBone]:
        start_bone = bones[-1]
        end_bone = bones[0]
        diff = (start_bone.global_loc - end_bone.global_loc_tail)
        direction = diff.normalized()

        arm = self.bone.arm
        roll = self.bone.edit_bone.roll

        height = self.bone.edit_bone.length * 2
        side = bone_get_side(self.bone)
        bone_index = 0
        spline_index = 0
        center_bones = []
        pp = []

        for center, left, right in points:
            base_name = f'Spline_{bone_index}_IK_TWEAKER_'

            center_bone = arm.edit_bones.new(base_name + 'CENTER' + side)
            left_bone = arm.edit_bones.new(base_name + 'LEFT' + side)
            right_bone = arm.edit_bones.new(base_name + 'RIGHT' + side)
            bone_disable_deform([center_bone, left_bone, right_bone])

            pp.append((center_bone.name, left_bone.name, right_bone.name))

            self.coll.add_ik(center_bone)
            self.coll.add_ik(left_bone)
            self.coll.add_ik(right_bone)

            center_bones.append(center_bone)

            self.styles.add(center_bone.name, ShapesEnum.SphereDirWire)
            s = self.styles.add(left_bone.name, ShapesEnum.SphereDirWire)
            s.scale = (.5, .5, .5)
            s = self.styles.add(right_bone.name, ShapesEnum.SphereDirWire)
            s.scale = (.5, .5, .5)

            left_bone.parent = center_bone
            right_bone.parent = center_bone

            dire = direction * height

            center_bone.tail = center - dire
            left_bone.tail = left - dire
            right_bone.tail = right - dire

            center_bone.head = center
            left_bone.head = left
            right_bone.head = right

            center_bone.roll = roll
            left_bone.roll = roll
            right_bone.roll = roll

            self._indexs.append((curve_obj, left_bone.name, spline_index))
            self._indexs.append((curve_obj, center_bone.name, spline_index + 1))
            self._indexs.append((curve_obj, right_bone.name, spline_index + 2))

            bone_index += 1
            spline_index += 3

        global curve_bones_control
        curve_bones_control = tuple(pp)

        return center_bones

    def execute_edit(self, context: bpy.types.Context):
        self._bones_parent.clear()
        self._indexs.clear()
        self._copy_rotation.clear()
        global curve_arm
        curve_arm = self.bone.obj.name
        bones = list(self.get_bones(self.bone))

        sp_fit_bones = []
        sp_original_bones = []
        sp_switch_bones = []

        rna_idprop_ui_create(self.bone.obj, 'zenu_stretching', default=0, min=0, max=1, subtype='FACTOR')

        for bone in bones:
            curve_bones.append(bone.name)
            e_bone = bone.edit_bone
            sp_switch_bone = bone_clone(e_bone, postfix='_SPLINE_SWITCH_MCH')

            bone_disable_deform([sp_switch_bone])

            e_bone.use_connect = False
            e_bone.parent = sp_switch_bone
            sp_switch_bones.append(sp_switch_bone)

            self._bones_parent.append(SplineBind(
                fit='',
                original='',
                deform=sp_switch_bone.name
            ))

        bone_connect(sp_fit_bones, revers=True)
        bone_connect(sp_original_bones, revers=True)
        bone_connect(sp_switch_bones, revers=True)

        self._spline_original_constraint_bone = sp_switch_bones[0].name

        points, curve_obj = self.generate_spline(bones, self.spline_point_count)

        controls_bone = self.create_controls(bones, points, curve_obj)

        for bone in bones:
            self._copy_rotation.append(CopyRotation(
                bone=bone.name,
                targets=[bone.name for bone in controls_bone],
            ))

    def execute_pose(self, context: bpy.types.Context):
        bones = list(self.get_bones(self.bone))
        arm_obj = self.bone.obj
        curve_obj = None

        for curve_obj, bone_name, point_index in self._indexs:
            constraint: bpy.types.HookModifier = curve_obj.modifiers.new('SplineIk', type='HOOK')
            constraint.object = arm_obj
            constraint.subtarget = bone_name
            constraint.vertex_indices_set([point_index])
            arm_obj.pose.bones[bone_name]['zenu_angle'] = 0.0

        target_bone = arm_obj.pose.bones[self._spline_original_constraint_bone]
        constraint: bpy.types.SplineIKConstraint = target_bone.constraints.new(type='SPLINE_IK')
        constraint.chain_count = len(bones)
        constraint.target = curve_obj
        constraint.y_scale_mode = 'BONE_ORIGINAL'

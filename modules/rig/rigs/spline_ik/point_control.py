import bpy
from mathutils import Vector


class PointControl:
    _obj_arm: bpy.types.Object
    _arm: bpy.types.Armature
    _center_name: str = ''
    _center_scale_fix_name: str = ''
    _left_name: str = ''
    _right_name: str = ''
    _scale: float

    def __init__(self, arm: bpy.types.Object, scale: float = .02):
        self._obj_arm = arm
        self._arm = arm.data
        self._scale = scale

    def _create_bone(self, loc: Vector, name: str):
        bone = self._arm.edit_bones.new(name)
        bone.head = loc
        bone.tail = loc + Vector((0, 0, self._scale))
        bone.color.palette = 'THEME05'
        bone.use_deform = False

        return bone

    def create_bones(self, locs: tuple[Vector, Vector, Vector], name: str = 'IK-Spline'):
        center_pos, left_pos, right_pos = locs

        center = self._create_bone(center_pos, name)
        center_scale_fix = self._create_bone(center_pos, center.name + '_scale_fix')
        left = self._create_bone(left_pos, name)
        right = self._create_bone(right_pos, name)

        center_scale_fix.parent = center
        center_scale_fix.inherit_scale = 'NONE'

        left.parent = center
        left.inherit_scale = 'NONE'

        right.parent = center
        right.inherit_scale = 'NONE'

        self._center_name = center.name
        self._center_scale_fix_name = center_scale_fix.name
        self._left_name = left.name
        self._right_name = right.name

    def get_pose_bones(self) -> tuple[bpy.types.PoseBone, bpy.types.PoseBone, bpy.types.PoseBone]:
        p = self._obj_arm.pose.bones
        return p[self._center_name], p[self._left_name], p[self._right_name]

    def get_edit_bone(self) -> tuple[bpy.types.PoseBone, bpy.types.PoseBone, bpy.types.PoseBone]:
        p = self._arm.edit_bones
        return p[self._center_name], p[self._left_name], p[self._right_name]

    def apply_theme(self, shape: bpy.types.Object):
        center, left, right = self.get_pose_bones()
        center_scale_fix = self._obj_arm.pose.bones[self._center_scale_fix_name]

        center.custom_shape = shape
        center.custom_shape_transform = center_scale_fix
        center.color.palette = 'THEME04'

        left.custom_shape = shape
        left.color.palette = 'THEME05'

        right.custom_shape = shape
        right.color.palette = 'THEME05'

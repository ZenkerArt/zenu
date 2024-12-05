import bpy
from .point_control import PointControl
from ...shapes import get_shape, ShapesEnum


class CurveControl:
    _spline: bpy.types.Curve
    _spline_obj: bpy.types.Object
    _arm_obj: bpy.types.Object
    _arm: bpy.types.Armature

    _spline_bind: list[tuple[str, list[int]]]
    _spline_controls: list[PointControl]

    def __init__(self, arm: bpy.types.Object, spline: bpy.types.Object):
        self._spline = spline.data
        self._spline_obj = spline
        self._arm_obj = arm
        self._arm = arm.data

        self._spline_bind = []
        self._spline_controls = []

    def _get_point_pos(self, index: int):
        point = self._spline.splines[0].bezier_points[index]
        mat = self._arm_obj.matrix_world.inverted()
        return (
            mat @ point.co,
            mat @ point.handle_left,
            mat @ point.handle_right
        )

    @staticmethod
    def _point_index(index: int):
        if index == 0:
            return index + 1
        else:
            return (index * 3) + 1

    def create_control(self, index: int, parent: str = None):
        loc, handle_left, handle_right = self._get_point_pos(index)
        point_control = PointControl(self._arm_obj)

        point_control.create_bones((loc, handle_left, handle_right))
        center, left, right = point_control.get_edit_bone()

        center_index = self._point_index(index)
        left_index = center_index - 1
        right_index = center_index + 1

        if parent:
            center.parent = self._arm.edit_bones[parent]

        self._spline_bind.append((center.name, [center_index]))
        self._spline_bind.append((left.name, [left_index]))
        self._spline_bind.append((right.name, [right_index]))

        self._spline_controls.append(point_control)

    def create_controls(self, parent: str = None):
        bpy.ops.object.mode_set(mode='EDIT')
        for i in range(len(self._spline.splines[0].bezier_points)):
            self.create_control(i, parent=parent)

        bpy.ops.object.mode_set(mode='POSE')

        for name, indices in self._spline_bind:
            hook: bpy.types.HookModifier = self._spline_obj.modifiers.new(type='HOOK', name='Hook')
            hook.object = self._arm_obj
            hook.subtarget = name

            hook.vertex_indices_set(indices)

        shape = get_shape('WGT-CubeWire')
        for i in self._spline_controls:
            i.apply_theme(shape)

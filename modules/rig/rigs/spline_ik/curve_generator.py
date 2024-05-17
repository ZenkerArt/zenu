import bpy
from mathutils import Vector
from ...meta_bone import MetaBoneData


class Spline:
    _spline: bpy.types.Spline

    def __init__(self, spline: bpy.types.Spline):
        self._spline = spline

    def set_pos(self, index: int, loc: Vector, step: Vector):
        spline = self._spline

        spline.bezier_points[index].co = loc
        spline.bezier_points[index].handle_right = loc - step
        spline.bezier_points[index].handle_left = loc + step
        spline.bezier_points[index].handle_left_type = 'ALIGNED'
        spline.bezier_points[index].handle_right_type = 'ALIGNED'


class CurveGenerator:
    _start: MetaBoneData
    _bones: MetaBoneData.List

    def __init__(self, start: MetaBoneData, bones: MetaBoneData.List):
        self._start = start
        self._bones = bones

    def __repr__(self):
        return f'<SplineTree start="{self._start.pose_bone.name}" bones={len(self._bones)}>'

    def create_point(self, ):
        pass

    def generate_spline(self, spline_count: int) -> bpy.types.Object:
        curveData = bpy.data.curves.new('SplineRig', type='CURVE')
        curveData.dimensions = '3D'

        original_spline = curveData.splines.new('BEZIER')
        spline = Spline(original_spline)

        count = spline_count

        loc_start = self._start.global_loc_tail
        loc_end = self._bones[-1].global_loc

        dif = loc_end - loc_start
        length = dif.length
        direction = dif.normalized()
        p2p_length = length / (count - 1)
        step = direction * p2p_length
        handle_step = step / 3

        original_spline.bezier_points.add(count - 1)

        for i in range(0, count):
            loc = step * i
            spline.set_pos(i, loc_end - loc, handle_step)

        curve_ob = bpy.data.objects.new('SplineRig', curveData)
        bpy.context.scene.collection.objects.link(curve_ob)

        return curve_ob

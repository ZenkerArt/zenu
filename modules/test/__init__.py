import math
from typing import Any

import numpy as np

import blf
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from .draw_2d import Draw2D
from .draw_3d import Draw3D
from ...base_panel import BasePanel
from ...utils import update_window
from .bezier import Bezier, lerp
from .bezier_draw import bezier_draw

draw: 'Draw' = None
circle_size = .0001


class Draw:
    _is_enable: bool = False
    _render: Any = None
    _render_pixel: Any = None
    _font: int = 0
    _text_pos: Vector
    _a: Vector = Vector((0, 0, 0))
    _b: Vector = Vector((0, 0, 0))
    _c: Vector = Vector((0, 0, 0))
    _length: float = 0
    _k: float = 0
    _ka: float = 0
    vectors: list[Vector]
    drawer_2d: Draw2D
    drawer_3d: Draw3D

    def __init__(self):
        self.drawer_2d = Draw2D()
        self.drawer_3d = Draw3D()
        self._text_pos = Vector((0, 0, 0))
        self.vectors = []

    def angle_to_vector(self, angle: float, dist: float):
        return Vector(((math.sin(angle)) * dist, 0, (math.cos(angle)) * dist))

    def calc(self, point, start: Vector, target: Vector) -> tuple[Vector, float]:
        edge_angle = math.atan2(target.x - start.x, target.z - start.z)
        dist = point.distance
        angle = point.angle

        if target.x > 0:
            angle += edge_angle
        else:
            dist *= -1
            angle = math.pi - angle
            angle += edge_angle

        return self.angle_to_vector(angle, dist), edge_angle

    def get_pos_on_screen(self, pos: Vector):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                region_3d = area.spaces[0].region_3d
                for region in area.regions:
                    if region.type == 'WINDOW':
                        return view3d_utils.location_3d_to_region_2d(
                            region,
                            region_3d,
                            pos
                        )

    def _draw_point(self, pos: Vector, text: str, color=(1, 1, 0)):
        self.drawer_2d.draw_circle(pos, radius=20, color=color)
        self.drawer_2d.draw_text(pos - Vector((40, 0)), text, color=color)

    def _draw_pixel(self):
        text_pos = self.get_pos_on_screen(self._text_pos)
        point_c = bpy.context.scene.zenu_curve_point_c
        a = self.get_pos_on_screen(self._a)
        b = self.get_pos_on_screen(self._b)
        c = self.get_pos_on_screen(self._c)

        dist_b: float = bpy.context.scene.zenu_curve_point_b.distance
        dist_c: float = bpy.context.scene.zenu_curve_point_c.distance

        radius_a = 0
        radius_b = 0
        radius_c = 0

        if bpy.context.object or isinstance(bpy.context.object.data, bpy.types.Curve):
            curve = bpy.context.object.data
            size = curve.bevel_depth
            spline = bpy.context.object.data.splines.active

            radius_a = (size * spline.bezier_points[0].radius) * 1000
            radius_b = (size * spline.bezier_points[1].radius) * 1000
            radius_c = (size * spline.bezier_points[2].radius) * 1000

        text_left = Vector((0, a.y))
        self.drawer_2d.draw_text(text_left - Vector((-400, 0)), f'L = {self._length * 1000:.2f} mm')
        self.drawer_2d.draw_text(text_left - Vector((-400, 30)), f'K = {self._k:.2f}(A = {self._ka:.2f})')

        self.drawer_2d.draw_circle(c, radius=20)
        self.drawer_2d.draw_text(text_pos + Vector((0, 20)), f'{round(math.degrees(point_c.angle), 2)} °')
        self._draw_point(a, f'A{" " * 10}R = {radius_a:.2f} mm', color=(.99609375, .53125, .52734375))
        self._draw_point(b, f'B{" " * 14}R = {radius_b:.2f} mm', color=(.8671875, .875, 1))
        self._draw_point(c, f'C{" " * 10}R = {radius_c:.2f} mm', color=(0, 1, 0))

        self.drawer_2d.draw_text(lerp(a, b, .5), f'{" " * 10}{dist_b * 1000:.2f} mm')
        self.drawer_2d.draw_text(lerp(b, c, .5), f'{" " * 10}{dist_c * 1000:.2f} mm')

    def _move_spline(self):
        if bpy.context.object is None or not isinstance(bpy.context.object.data, bpy.types.Curve):
            return

        points = bpy.context.object.data.splines.active.bezier_points
        points[0].co = self._a
        points[1].co = self._b
        points[2].co = self._c

    def _draw_curve_comb(self):
        if bpy.context.object is None or not isinstance(bpy.context.object.data, bpy.types.Curve):
            return

        if not bpy.context.scene.zenu_curve_comb_show:
            return
        spline = bpy.context.object.data.splines.active
        points = spline.bezier_points

        sum_k = 0
        sum_ka = 0
        sum_count = 0

        for index, i in enumerate(points):
            if index + 1 >= len(points):
                break
            p0 = i.co
            p1 = i.handle_right
            p2 = points[index + 1].handle_left
            p3 = points[index + 1].co
            curve = Bezier(*np.array((
                (p0[0], p0[2]),
                (p1[0], p1[2]),
                (p2[0], p2[2]),
                (p3[0], p3[2]),
            )))
            k, ka, c = bezier_draw(curve, self.drawer_3d, scale=bpy.context.scene.zenu_curve_comb_scale,
                                   steps=bpy.context.scene.zenu_curve_comb_steps)
            sum_count += c
            sum_k += k
            sum_ka += ka

        self._length = spline.calc_length()
        self._k = sum_k / sum_count
        self._ka = sum_ka / sum_count

    def _draw(self):
        pointB = bpy.context.scene.zenu_curve_point_b
        pointC = bpy.context.scene.zenu_curve_point_c
        circle_radius = bpy.context.scene.zenu_circle_radius
        point_a = Vector((0, 0, bpy.context.scene.zenu_curve_height))
        point_b = self.angle_to_vector(pointB.angle, pointB.distance * -1)
        point_b += point_a

        v3, edge_angle = self.calc(pointC, point_a, point_b)
        point_c = point_b + v3
        v4 = self.angle_to_vector(edge_angle, pointC.distance)

        circle_p1 = point_b + self.angle_to_vector(edge_angle, circle_radius)
        circle_ang = -pointC.angle if point_b.x < 0 else pointC.angle
        center = self.drawer_3d.draw_circle(point_b, edge_angle, circle_ang, (circle_p1 - point_b).length)

        self._a = point_a
        self._b = point_b
        self._c = point_c

        self._text_pos = center + Vector((-.0005, 0, -.0005))
        self.drawer_3d.draw_lines([
            point_a, point_b,
            point_b, point_b + v3,
            point_b, point_b + v4
        ], color=(.26171875, .546875, .828125))
        self._draw_curve_comb()
        self._move_spline()

    def compute(self):
        point1 = bpy.context.scene.zenu_curve_point_b
        point2 = bpy.context.scene.zenu_curve_point_c
        v1 = Vector((0, 0, bpy.context.scene.zenu_curve_height))
        angle = math.radians(point1.angle)
        dist = point1.distance * -1
        v2 = self.angle_to_vector(angle, dist)
        v2 += v1
        v3, edge_angle = self.calc(point2, v1, v2)
        self.vectors.clear()
        self.vectors.append(v1)
        self.vectors.append(v2)
        self.vectors.append(v2 + v3)

    def draw_pixel(self):
        try:
            self._draw_pixel()
        except Exception as e:
            print(f'View error: {e}')
            self.disable()

    def draw(self):
        try:
            self._draw()
        except Exception as e:
            print(f'View error: {e}')
            self.disable()

    def disable(self):
        self._is_enable = False
        try:
            if self._render:
                bpy.types.SpaceView3D.draw_handler_remove(self._render, 'WINDOW')
                bpy.types.SpaceView3D.draw_handler_remove(self._render_pixel, 'WINDOW')
                update_window()
        except Exception as e:
            print(f'Disable view error: {e}')

    def enable(self):
        if self._is_enable:
            return
        self._is_enable = True
        self._render = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')
        self._render_pixel = bpy.types.SpaceView3D.draw_handler_add(self.draw_pixel, (), 'WINDOW', 'POST_PIXEL')
        update_window()

    def toggle(self):
        if self._is_enable:
            self.disable()
        else:
            self.enable()

    @property
    def is_enable(self):
        return self._is_enable


class ZENU_OT_create_curve(bpy.types.Operator):
    bl_label = 'Create Curve'
    bl_idname = 'zenu.create_curve'

    def execute(self, context: bpy.types.Context):
        draw.compute()

        curve_data = bpy.data.curves.new('myCurve', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 12

        polyline = curve_data.splines.new('BEZIER')
        polyline.bezier_points.add(len(draw.vectors) - 1)
        for i, coord in enumerate(draw.vectors):
            x, y, z = coord
            polyline.bezier_points[i].co = (x, y, z)

        # create Object
        curveOB = bpy.data.objects.new('myCurve', curve_data)
        curve_data.bevel_depth = 0.001
        context.scene.collection.objects.link(curveOB)
        bpy.context.view_layer.objects.active = curveOB
        curveOB.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
        bpy.ops.object.mode_set(mode='OBJECT')
        draw.enable()
        return {'FINISHED'}


class ZENU_OT_enable_view(bpy.types.Operator):
    bl_label = 'Toggle View'
    bl_idname = 'zenu.enbale_view'

    def execute(self, context: bpy.types.Context):
        draw.obj = context.active_object
        draw.toggle()
        return {'FINISHED'}


class ZENU_PT_curvature_creator(BasePanel):
    bl_label = 'Curvature Creator'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column_flow(align=True)
        col.operator(ZENU_OT_enable_view.bl_idname, depress=draw.is_enable)
        col.prop(context.scene, 'zenu_curve_height', slider=True)
        col.prop(context.scene, 'zenu_circle_radius', slider=True)

        point1 = context.scene.zenu_curve_point_b
        point2 = context.scene.zenu_curve_point_c

        layout.label(text='Point B')
        col = layout.column_flow(align=True)
        col.prop(point1, 'angle', slider=True)
        col.prop(point1, 'distance', slider=True)

        layout.label(text='Point C')
        col = layout.column_flow(align=True)
        col.prop(point2, 'angle', slider=True)
        col.prop(point2, 'distance', slider=True)


class ZENU_PT_curvature_creator_curve(BasePanel):
    bl_label = 'Curvature'
    bl_parent_id = 'ZENU_PT_curvature_creator'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column_flow(align=True)
        col.operator(ZENU_OT_create_curve.bl_idname)
        col.prop(context.scene, 'zenu_curve_comb_show', icon='RESTRICT_VIEW_ON')
        col.prop(context.scene, 'zenu_curve_comb_steps', slider=True)
        col.prop(context.scene, 'zenu_curve_comb_scale', slider=True)
        col.prop(context.scene, 'zenu_active_curve_bevel', slider=True)

class CurvePointInfo(bpy.types.PropertyGroup):
    distance: bpy.props.FloatProperty(name='Distance', soft_min=.01, soft_max=.05, subtype='DISTANCE')
    angle: bpy.props.FloatProperty(name='Angle', soft_max=math.pi / 2, soft_min=-math.pi / 2, subtype='ANGLE')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_enable_view,
    ZENU_OT_create_curve,
    ZENU_PT_curvature_creator,
    ZENU_PT_curvature_creator_curve,
    CurvePointInfo
))

draw = Draw()


def update_curve_radius(self, context: bpy.types.Context):
    if bpy.context.object is None or not isinstance(bpy.context.object.data, bpy.types.Curve):
        return
    curve_data = bpy.context.object.data
    curve_data.bevel_depth = context.scene.zenu_active_curve_bevel


def register():
    global draw
    reg()

    bpy.types.Scene.zenu_curve_point_b = bpy.props.PointerProperty(type=CurvePointInfo)
    bpy.types.Scene.zenu_curve_point_c = bpy.props.PointerProperty(type=CurvePointInfo)
    bpy.types.Scene.zenu_curve_height = bpy.props.FloatProperty(name='Height', soft_min=.01, soft_max=.05,
                                                                subtype='DISTANCE')

    bpy.types.Scene.zenu_circle_radius = bpy.props.FloatProperty(name='Circle Radius', soft_min=.01, soft_max=.05,
                                                                 subtype='DISTANCE', default=.01)
    bpy.types.Scene.zenu_curve_comb_steps = bpy.props.IntProperty(name='Comb Steps', min=1, soft_max=100, default=50)
    bpy.types.Scene.zenu_curve_comb_scale = bpy.props.FloatProperty(name='Comb Scale', min=.1 / 1000, soft_max=2 / 1000,
                                                                    subtype='DISTANCE', default=.00005)

    bpy.types.Scene.zenu_curve_comb_show = bpy.props.BoolProperty(name='Comb Show', default=False)

    bpy.types.Scene.zenu_active_curve_bevel = bpy.props.FloatProperty(name='Curve Radius', soft_min=.1 / 1000,
                                                                      soft_max=10 / 1000, update=update_curve_radius,
                                                                      subtype='DISTANCE')


def unregister():
    draw.disable()
    unreg()

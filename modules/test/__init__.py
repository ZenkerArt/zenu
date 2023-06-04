import math
from typing import Any

import blf
from bpy_extras import view3d_utils
# from gpu_extras.presets import draw_circle_2d
from mathutils import Vector, Matrix, Euler
import os
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from ...utils import update_window
from ...base_panel import BasePanel
from .circle import draw_circle

draw: 'Draw' = None
circle_size = .0001


class Draw:
    _is_enable: bool = False
    _render: Any = None
    _render_pixel: Any = None
    _shader: Any = None
    _shader2d: Any = None
    _font: int = 0
    _text_pos: Vector
    _a: Vector = Vector((0, 0, 0))
    _b: Vector = Vector((0, 0, 0))
    _c: Vector = Vector((0, 0, 0))
    obj: bpy.types.Object = None
    vectors: list[Vector]

    def __init__(self):
        self._shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self._shader2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self._text_pos = Vector((0, 0, 0))
        self.vectors = []

    def angle_to_vector(self, angle: float, dist: float):
        return Vector(((math.sin(angle) / math.pi) * dist, 0, (math.cos(angle) / math.pi) * dist))

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

    def _draw_point(self, pos: Vector, text: str, font: int = 0):
        blf.position(font, pos.x - 40, pos.y, 0)
        blf.size(font, 18)
        blf.color(font, 1, 1, 1, 1)
        blf.draw(font, text)
        self._draw_circle_2d(pos, radius=20)

    def _draw_pixel(self):
        gpu.matrix.load_matrix(gpu.matrix.get_model_view_matrix())
        text_pos = self.get_pos_on_screen(self._text_pos)
        point_c = bpy.context.scene.zenu_curve_pointC
        a = self.get_pos_on_screen(self._a)
        b = self.get_pos_on_screen(self._b)
        c = self.get_pos_on_screen(self._c)
        self._draw_circle_2d(c, radius=20)

        font = 0
        blf.position(font, text_pos.x, text_pos.y, 0)
        blf.size(font, 18)
        blf.color(font, 1, 1, 1, 1)
        blf.draw(font, f'{round(math.degrees(point_c.angle), 2)} °')

        self._draw_point(a, 'A')
        self._draw_point(b, 'B')
        self._draw_point(c, 'C')

    def _draw_circle_2d(self, pos: Vector, start=0, end=math.pi * 2, radius: float = 1):
        self._shader2d.uniform_float("color", (1, 1, 0, 1))
        segments = 24
        coords = []
        for i in range(0, segments):
            mul = (1.0 / (segments - 1)) * end

            prev = (
                math.sin(start + i * mul) * radius + pos.x,
                math.cos(start + i * mul) * radius + pos.y
            )
            coords.append(prev)

        batch = batch_for_shader(self._shader2d, 'LINE_STRIP', {"pos": coords})
        self._shader2d.bind()
        self._shader2d.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
        gpu.state.line_width_set(2)
        batch.draw(self._shader2d)

    def _draw_circle(self, pos: Vector, start=0, end=math.pi * 2, radius: float = 1):
        self._shader.uniform_float("color", (1, 1, 0, 1))
        segments = 24
        coords = []
        for i in range(0, segments):
            mul = (1.0 / (segments - 1)) * end

            prev = (
                math.sin(start + i * mul) * radius + pos.x,
                pos.y,
                math.cos(start + i * mul) * radius + pos.z
            )
            coords.append(prev)

        batch = batch_for_shader(self._shader, 'LINE_STRIP', {"pos": coords})
        batch.draw(self._shader)
        return Vector(coords[int(len(coords) / 2)])

    def _draw_lines(self, coords: list[Vector]):
        self._shader.uniform_float("color", (1, 1, 0, 1))
        batch = batch_for_shader(self._shader, 'LINES', {"pos": coords})
        gpu.state.line_width_set(2)
        batch.draw(self._shader)

    def _move_spline(self):
        if bpy.context.object is None or not isinstance(bpy.context.object.data, bpy.types.Curve):
            return

        points = bpy.context.object.data.splines.active.bezier_points
        points[0].co = self._a
        points[1].co = self._b
        points[2].co = self._c

    def _draw(self):
        pointB = bpy.context.scene.zenu_curve_pointB
        pointC = bpy.context.scene.zenu_curve_pointC
        circle_radius = bpy.context.scene.zenu_circle_radius
        point_a = Vector((0, 0, bpy.context.scene.zenu_curve_height))
        point_b = self.angle_to_vector(pointB.angle, pointB.distance * -1)
        point_b += point_a

        v3, edge_angle = self.calc(pointC, point_a, point_b)
        point_c = point_b + v3

        v4 = self.angle_to_vector(edge_angle, pointC.distance)

        circle_p1 = point_b + self.angle_to_vector(edge_angle, circle_radius)
        circle_ang = -pointC.angle if point_b.x < 0 else pointC.angle
        center = self._draw_circle(point_b, edge_angle, circle_ang, (circle_p1 - point_b).length)

        self._a = point_a
        self._b = point_b
        self._c = point_c
        self._text_pos = center + Vector((-.0005, 0, -.0005))

        self._draw_lines([
            point_a, point_b,
            point_b, point_b + v3,
            point_b, point_b + v4
        ])
        self._move_spline()


    def compute(self):
        point1 = bpy.context.scene.zenu_curve_pointB
        point2 = bpy.context.scene.zenu_curve_pointC
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

        curveData = bpy.data.curves.new('myCurve', type='CURVE')
        curveData.dimensions = '3D'
        curveData.resolution_u = 12

        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add(len(draw.vectors) - 1)
        for i, coord in enumerate(draw.vectors):
            x, y, z = coord
            polyline.bezier_points[i].co = (x, y, z)

        # create Object
        curveOB = bpy.data.objects.new('myCurve', curveData)
        curveData.bevel_depth = 0.01
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


class ZENU_PT_view(BasePanel):
    bl_label = 'view'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column_flow(align=True)
        col.operator(ZENU_OT_create_curve.bl_idname)
        col.operator(ZENU_OT_enable_view.bl_idname, depress=draw.is_enable)
        col.prop(context.scene, 'zenu_curve_height', slider=True)
        col.prop(context.scene, 'zenu_circle_radius', slider=True)

        point1 = context.scene.zenu_curve_pointB
        point2 = context.scene.zenu_curve_pointC

        layout.label(text='Point B')
        col = layout.column_flow(align=True)
        col.prop(point1, 'angle', slider=True)
        col.prop(point1, 'distance', slider=True)

        layout.label(text='Point C')
        col = layout.column_flow(align=True)
        col.prop(point2, 'angle', slider=True)
        col.prop(point2, 'distance', slider=True)


class CurvePointInfo(bpy.types.PropertyGroup):
    distance: bpy.props.FloatProperty(name='Distance', soft_min=.01, soft_max=.05, subtype='DISTANCE')
    angle: bpy.props.FloatProperty(name='Angle', soft_max=math.pi / 2, soft_min=-math.pi / 2, subtype='ANGLE')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_enable_view,
    ZENU_OT_create_curve,
    ZENU_PT_view,
    CurvePointInfo
))

draw = Draw()


def register():
    global draw
    reg()

    bpy.types.Scene.zenu_curve_pointB = bpy.props.PointerProperty(type=CurvePointInfo)
    bpy.types.Scene.zenu_curve_pointC = bpy.props.PointerProperty(type=CurvePointInfo)
    bpy.types.Scene.zenu_curve_height = bpy.props.FloatProperty(name='Height', soft_min=.01, soft_max=.05,
                                                                subtype='DISTANCE')

    bpy.types.Scene.zenu_circle_radius = bpy.props.FloatProperty(name='Circle Radius', soft_min=.01, soft_max=.05,
                                                                 subtype='DISTANCE', default=.01)


def unregister():
    draw.disable()
    unreg()

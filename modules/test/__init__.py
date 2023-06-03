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
from .circle import draw_circle_2d
import numpy as np
draw: 'Draw' = None



#from here https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


class Draw:
    _is_enable: bool = False
    _render: Any = None
    _render_pixel: Any = None
    _shader: Any = None
    _font: int = 0
    _text_pos: Vector
    obj: bpy.types.Object = None
    vectors: list[Vector]

    def __init__(self):
        self._shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self._text_pos = Vector((0, 0, 0))
        self.vectors = []

    def angle_to_vector(self, angle: float, dist: float):
        return Vector(((math.sin(angle) / math.pi) * dist, 0, (math.cos(angle) / math.pi) * dist))

    def calc(self, point, start: Vector, target: Vector) -> tuple[Vector, float]:
        edge_angle = math.atan2(target.x - start.x, target.z - start.z)
        dist = point.distance
        angle = math.radians(point.angle)

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

    def _draw_pixel(self):
        point2 = bpy.context.scene.zenu_curve_point2
        text_pos = self.get_pos_on_screen(self._text_pos)
        gpu.matrix.load_matrix(gpu.matrix.get_model_view_matrix())

        blf.position(self._font, text_pos.x, text_pos.y, 0)
        blf.size(self._font, 18)
        blf.color(self._font, 1, 1, 1, 1)
        blf.draw(self._font, f'{round(point2.angle, 2)}')

    def _draw(self):
        point1 = bpy.context.scene.zenu_curve_point1
        point2 = bpy.context.scene.zenu_curve_point2
        v1 = Vector((0, 0, bpy.context.scene.zenu_curve_height))

        angle = math.radians(point1.angle)
        dist = point1.distance * -1
        v2 = self.angle_to_vector(angle, dist)
        v2 += v1

        v3, edge_angle = self.calc(point2, v1, v2)

        rot = Matrix.Rotation(math.radians(90), 4, 'X')
        draw_circle_2d(v2 + v3, (1, 1, 1, 1), .05, segments=40, mat=rot)
        draw_circle_2d(v2, (1, 1, 1, 1), .05, segments=40, mat=rot)

        v4 = self.angle_to_vector(edge_angle, point2.distance)

        self._text_pos = ((v2 + v4) + (v2 + v3)) / 2 - Vector((0, 0, .2))

        coords = [v1, v2]
        coords.append(v2)
        coords.append(v2 + v3)
        coords.append(v2)
        coords.append(v2 + v4)

        # blf.draw(self._font, "Hello World")

        self._shader.uniform_float("color", (1, 1, 0, 1))
        batch = batch_for_shader(self._shader, 'LINES', {"pos": coords})
        batch.draw(self._shader)

    def compute(self):
        point1 = bpy.context.scene.zenu_curve_point1
        point2 = bpy.context.scene.zenu_curve_point2
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
    bl_label = 'Curve Create'
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
        col.operator(ZENU_OT_enable_view.bl_idname, depress=draw.is_enable)
        col.operator(ZENU_OT_create_curve.bl_idname)
        col.prop(context.scene, 'zenu_curve_height', slider=True)

        point1 = context.scene.zenu_curve_point1
        point2 = context.scene.zenu_curve_point2

        layout.label(text='Point B')
        col = layout.column_flow(align=True)
        col.prop(point1, 'angle', slider=True)
        col.prop(point1, 'distance', slider=True)

        layout.label(text='Point C')
        col = layout.column_flow(align=True)
        col.prop(point2, 'angle', slider=True)
        col.prop(point2, 'distance', slider=True)


class CurvePointInfo(bpy.types.PropertyGroup):
    distance: bpy.props.FloatProperty(name='Distance', soft_max=40, soft_min=-40)
    angle: bpy.props.FloatProperty(name='Angle', soft_max=90, soft_min=-90)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_enable_view,
    ZENU_OT_create_curve,
    ZENU_PT_view,
    CurvePointInfo
))


def register():
    global draw
    if draw is None:
        draw = Draw()
    reg()

    bpy.types.Scene.zenu_curve_point1 = bpy.props.PointerProperty(type=CurvePointInfo)
    bpy.types.Scene.zenu_curve_point2 = bpy.props.PointerProperty(type=CurvePointInfo)
    bpy.types.Scene.zenu_curve_height = bpy.props.FloatProperty(name='Height', soft_min=0, soft_max=10)


def unregister():
    draw.disable()
    unreg()

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import bpy
import gpu
from bl_math import lerp
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ...base_panel import BasePanel
from ...utils import update_window
from functools import partial


def create_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
    vert_out.smooth('VEC3', "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant('MAT4', "viewProjectionMatrix")
    shader_info.push_constant('VEC3', "offset")
    shader_info.push_constant('VEC3', "color")
    shader_info.push_constant('FLOAT', "size")
    shader_info.vertex_in(0, 'VEC3', "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, 'VEC4', "FragColor")

    shader_info.vertex_source(
        "void main()"
        "{"
        "  pos = position;"
        "  gl_Position = viewProjectionMatrix * vec4(offset + (position * size), 1.0f);"
        "}"
    )

    shader_info.fragment_source(
        "void main()"
        "{"
        "  FragColor = vec4(color, 1.0);"
        "}"
    )

    shader = gpu.shader.create_from_info(shader_info)
    del vert_out
    del shader_info
    return shader


def get_draw_test() -> 'DrawTest':
    return bpy.context.scene.zenu_draw_test


class GpuDrawer(ABC):
    _handler: Any = None

    @abstractmethod
    def draw(self):
        pass

    def _register(self):
        if self._handler is not None:
            return

        self._handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')
        update_window()

    def _unregister(self):
        if self._handler is None:
            return

        bpy.types.SpaceView3D.draw_handler_remove(self._handler, 'WINDOW')
        self._handler = None
        update_window()

    def register(self):
        self._register()

    def unregister(self):
        self._unregister()


@dataclass
class Beizer:
    p0: Vector = field(default_factory=partial(Vector, (0, 0, 0)))
    p1: Vector = field(default_factory=partial(Vector, (0, 0, 0)))
    p2: Vector = field(default_factory=partial(Vector, (0, 0, 0)))
    p3: Vector = field(default_factory=partial(Vector, (0, 0, 0)))
    attributes: dict[str, float] = field(default_factory=lambda: {'angle': 0})


@dataclass()
class BeizerPoint:
    pos: Vector
    time: float = 0
    attributes: dict[str, float] = field(default_factory=lambda: {'angle': 0})
    next_point: 'BeizerPoint' = None
    prev_point: 'BeizerPoint' = None


class ShaderDraw:
    _shader: gpu.types.GPUShader
    _batch: gpu.types.GPUBatch

    @classmethod
    def from_shader(cls, props: dict[str, Any], shader: gpu.types.GPUShader, type='LINE_STRIP'):
        self = cls()
        self._shader = shader
        self._batch = batch_for_shader(self._shader, type, props)
        return self

    @classmethod
    def from_builtin(cls, coords: list[Vector | tuple[float, float, float]], type='LINE_STRIP'):
        self = cls()
        self._shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        self._batch = batch_for_shader(self._shader, type, {"pos": coords})
        return self

    @property
    def shader(self) -> gpu.types.GPUShader:
        return self._shader

    def draw(self):
        # self._shader.uniform_float("color", (1, 1, 0, 1))
        self._batch.draw(self._shader)


def create_sphere():
    coords = []

    for i in range(0, 32):
        offset = math.tau * (i / 32)
        coords.append((math.sin(offset), math.cos(offset), 0))

    for i in range(0, 32):
        offset = math.tau * (i / 32)
        coords.append((math.sin(offset), 0, math.cos(offset)))

    for i in range(0, 32):
        offset = math.tau * (i / 32)
        coords.append((0, math.sin(offset), math.cos(offset)))

    coords.extend((
        (0, 0, -1),
        (0, 0, 1),

        (0, -1, 0),
        (0, 1, 0),

        (-1, 0, 0),
        (1, 0, 0),
    ))

    return coords


@dataclass()
class Point:
    pos: Vector
    color: Vector = (0, 1, 0)
    scale: float = .01


class CurveDraw:
    _points: list[Point]
    _beizer_points: list[BeizerPoint]
    _beizer_list: list[Beizer]

    def __init__(self):
        self._beizer_list = [
            Beizer(
                p0=Vector((-5, 0, -1)),
                p1=Vector((-1, 0, 1)),
                p2=Vector((1, 0, 1)),
                p3=Vector((1, 0, -1))
            )

        ]
        self._beizer_points = []
        self.rebuild()

    def calc_beizer(self, beizer: Beizer, t: float) -> BeizerPoint:
        p0 = beizer.p0
        p1 = beizer.p1
        p2 = beizer.p2
        p3 = beizer.p3

        a = p0.lerp(p1, t)
        b = p1.lerp(p2, t)

        c = p2.lerp(p3, t)
        d = a.lerp(b, t)

        e = b.lerp(c, t)
        return BeizerPoint(
            pos=d.lerp(e, t),
            time=t
        )

    def beizer_to_points(self, beizer: Beizer, quality: int = 60):
        points = []
        for i in range(0, quality + 1):
            points.append(self.calc_beizer(beizer, i / quality))
        return points

    def beizer_controllers(self, beizer: Beizer):
        coords = [beizer.p0, beizer.p1, beizer.p2, beizer.p3]
        return coords

    def add(self, bezier: Beizer):
        self._beizer_list.append(bezier)

    def clear(self):
        self._beizer_list.clear()
        self._beizer_points.clear()

    def rebuild(self):
        self._beizer_points.clear()

        prev_beizer = None
        prev_value = 0
        for index, beizer in enumerate(self._beizer_list):
            points = self.beizer_to_points(beizer)
            for key, value in beizer.attributes.items():
                if prev_beizer:
                    prev_value = prev_beizer.attributes[key]

                for index, point in enumerate(points):
                    point.attributes[key] = lerp(value, prev_value, point.time)

            if index > 0:
                del points[0]

            self._beizer_points.extend(reversed(points))
            prev_beizer = beizer

        points = self._beizer_points
        for index, point in enumerate(points):
            # self.add_point(point.pos, color=(0, 0, 1), size=.02)
            try:
                point.next_point = points[index - 1]
            except IndexError:
                pass
            try:
                point.prev_point = points[index + 1]
            except IndexError:
                pass

    def get_closer_point(self, pos: Vector) -> BeizerPoint:
        length = float('inf')

        current_point = None

        for point in self._beizer_points:
            diff = point.pos - pos
            leng = abs(diff.length)

            if leng < length:
                length = leng
                current_point = point
        return current_point

    def get_closer_point_lerp(self, pos: Vector) -> BeizerPoint:
        current_point = self.get_closer_point(pos)
        if current_point.prev_point is None:
            return current_point

        prev_point = current_point.prev_point
        next_point = current_point.next_point

        full_length = abs((prev_point.pos - next_point.pos).length)

        pos_point_length = abs(1 - abs((pos - next_point.pos).length) / full_length)

        new_pos = prev_point.pos.lerp(next_point.pos, pos_point_length)

        new_attributes = {}
        for key, next_value in next_point.attributes.items():
            prev_value = next_point.next_point.attributes[key]

            new_attributes[key] = lerp(prev_value, next_value, pos_point_length)

        return BeizerPoint(
            pos=new_pos,
            attributes=new_attributes
        )


class ZENU_PT_curve(BasePanel):
    bl_label = 'Curve'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        layout.prop(context.scene.zenu_draw_test, 't')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_curve,
))


def register():
    reg()


def unregister():
    unreg()

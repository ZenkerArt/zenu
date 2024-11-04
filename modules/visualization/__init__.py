import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ...utils import update_window


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


class Visualization(GpuDrawer):
    draws: list[ShaderDraw]
    _point: ShaderDraw
    _points: list[Point]

    def __init__(self):
        self.draws = []
        self._point = ShaderDraw.from_shader({'position': create_sphere()}, create_shader(), type='LINES')
        self._points = []
        self.rebuild()

    def clear(self):
        self.draws.clear()
        self._points.clear()

    def rebuild(self):
        self.draws.clear()
        self._points.clear()

    def add_point(self, pos: Vector, color: Vector = (0, 1, 0), size: float = 0.01):
        self._points.append(Point(
            pos=pos,
            color=color,
            scale=size
        ))

    def draw(self):
        for i in self.draws:
            shad = i.shader
            shad.uniform_float('color', (1, 1, 1, 1))
            i.draw()

        shad = self._point.shader
        matrix = bpy.context.region_data.perspective_matrix
        shad.uniform_float("viewProjectionMatrix", matrix)

        for i in self._points:
            shad.uniform_float('color', i.color)
            shad.uniform_float('size', i.scale)
            shad.uniform_float('offset', i.pos)
            self._point.draw()


visualization = Visualization()


def register():
    visualization.register()


def unregister():
    visualization.unregister()

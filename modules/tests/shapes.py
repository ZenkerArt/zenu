import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ...utils import update_window


class GpuDrawer(ABC):
    _handler: Any = None

    @abstractmethod
    def draw(self):
        pass

    def _draw(self):
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


def create_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
    vert_out.smooth('VEC3', "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant('MAT4', "viewProjectionMatrix")
    shader_info.push_constant('FLOAT', "brightness")
    shader_info.push_constant('VEC3', "offset")
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
        "  FragColor = vec4(vec3(1, 1, 0) * brightness, 1.0);"
        "}"
    )

    shader = gpu.shader.create_from_info(shader_info)
    del vert_out
    del shader_info
    return shader


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


shad = create_shader()
batch = batch_for_shader(shad, 'LINES', {"position": create_sphere()})


@dataclass
class DrawObj:
    pos: Vector


class DrawTest(GpuDrawer):
    _objs: list[DrawObj]

    def __init__(self):
        self._objs = []

    def add_draw_obj(self, vec: Vector):
        obj = DrawObj(vec)
        self._objs.append(obj)
        update_window()
        return obj

    def clear(self):
        self._objs.clear()
        update_window()

    def draw(self):
        matrix = bpy.context.region_data.perspective_matrix
        shad.uniform_float("viewProjectionMatrix", matrix)
        shad.uniform_float("brightness", 0.5)
        gpu.state.depth_test_set('LESS')
        for i in self._objs:
            shad.uniform_float("size", 0.5)
            shad.uniform_float("offset", i.pos)
            batch.draw(shad)

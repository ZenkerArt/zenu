from abc import abstractmethod, ABC
from typing import Any

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from ...utils import update_window


def create_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
    vert_out.smooth('VEC3', "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant('MAT4', 'ModelViewProjectionMatrix')
    # shader_info.push_constant('MAT4', "viewProjectionMatrix")
    shader_info.push_constant('VEC3', "offset")
    shader_info.push_constant('FLOAT', "size")
    shader_info.vertex_in(0, 'VEC3', "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, 'VEC4', "FragColor")

    shader_info.vertex_source(
        "void main()"
        "{"
        "  pos = position;"
        "  gl_Position = ModelViewProjectionMatrix * vec4(offset + (position), 1.0f);"
        "}"
    )

    shader_info.fragment_source(
        "void main()"
        "{"
        "  FragColor = vec4(vec3(1, 1, 0), 1.0);"
        "}"
    )

    shader = gpu.shader.create_from_info(shader_info)
    del vert_out
    del shader_info
    return shader


class GpuDrawer(ABC):
    _handler_ds: Any = None
    _handler_ge: Any = None

    @abstractmethod
    def draw(self):
        pass

    def _draw(self):
        pass

    def _register(self):
        if self._handler_ds is not None:
            return

        self._handler_ds = bpy.types.SpaceDopeSheetEditor.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
        self._handler_ge = bpy.types.SpaceGraphEditor.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
        update_window()

    def _unregister(self):
        if self._handler_ds is None:
            return

        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(self._handler_ds, 'WINDOW')
        bpy.types.SpaceGraphEditor.draw_handler_remove(self._handler_ge, 'WINDOW')
        self._handler_ds = None
        update_window()

    def register(self):
        self._register()

    def unregister(self):
        self._unregister()


class SpacesDrawer(GpuDrawer):
    shader: gpu.types.GPUShader
    batch: gpu.types.GPUBatch
    _spaces: list[int]

    def __init__(self):
        self._spaces = []
        shader = create_shader()
        batch = batch_for_shader(shader, 'LINE_STRIP', {'position': [(0, 0), (0, 1000)]})
        #
        # shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        # batch = batch_for_shader(shader, 'LINE_STRIP', {'pos': [(100,100),(268,130)]})

        self.shader = shader
        self.batch = batch

    def draw_space(self, start: int):
        context: bpy.types.Context = bpy.context
        scene = context.scene

        view2d = context.region.view2d
        height = context.region.height

        shader = self.shader
        batch = self.batch

        x, y = view2d.view_to_region(start, 1, clip=False)

        shader.uniform_float("offset", (x, 0, 0))
        batch.draw(shader)

    def add_space(self, frame: int):
        self._spaces.append(frame)

    def clear_spaces(self):
        self._spaces = []

    def draw(self):
        context: bpy.types.Context = bpy.context
        scene = context.scene
        for i in self._spaces:
            self.draw_space(i)


space = SpacesDrawer()

from abc import abstractmethod, ABC
from typing import Any

import bpy
import gpu
import mathutils
from bpy.app.handlers import persistent
from gpu_extras.batch import batch_for_shader
from .timeline import space
from ...utils import update_window
from ...base_panel import BasePanel
import requests


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


def create_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
    vert_out.smooth('VEC3', "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant('MAT4', "viewProjectionMatrix")
    shader_info.push_constant('VEC3', "offset")
    shader_info.push_constant('FLOAT', "size")
    shader_info.vertex_in(0, 'VEC3', "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, 'VEC4', "FragColor")

    shader_info.vertex_source(
        "void main()"
        "{"
        "  pos = position;"
        "  gl_Position = viewProjectionMatrix * vec4(offset + (position), 1.0f);"
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


class Draw(GpuDrawer):
    _shader: gpu.types.GPUShader
    _batches: list[gpu.types.GPUBatch]
    _data: dict

    def __init__(self):
        # self._shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        self._batches = []
        self._shader = create_shader()
        self._batch = batch_for_shader(self._shader, 'LINE_STRIP', {"position": [(0, 0, 0), (1, 1, 0)]})

    def update(self, positions: list[mathutils.Vector]):
        self._batches.append(batch_for_shader(self._shader, 'LINE_STRIP', {"position": positions}))

    def load_data(self, data: dict):
        self._data = data
        space.clear_spaces()

        for key, items in data['values']['_framesWidgets'].items():
            if not items: continue
            print(key)
            space.add_space(bpy.context.scene.frame_start + int(key) - 1)

    def load_frame(self, frame: int):
        try:
            self._batches.clear()
            data = self._data

            for i in data['values']['_framesWidgets'][str(frame)]:
                positions = []

                for i in i['values']['_points']:
                    positions.append(mathutils.Vector((i['x'], 1 - i['y'])))

                self.update(positions)
            update_window(all_w=True)
        except Exception as e:
            pass

    def load_frame_scene(self, scene: bpy.types.Scene):
        self.load_frame(scene.frame_current - scene.frame_start + 1)

    def draw(self):
        shad = self._shader
        scene = bpy.context.scene
        context = bpy.context
        camera = scene.camera

        data = camera.data.view_frame(scene=scene)

        mat = mathutils.Matrix.Scale(data[3].y - data[2].y, 4, (0, 1.0, 0))
        mat = mathutils.Matrix.Translation(data[2]) @ mat

        matrix = bpy.context.region_data.perspective_matrix
        shad.uniform_float("viewProjectionMatrix", matrix @ (camera.matrix_world @ mat))
        # shad.uniform_float("offset", vec)
        for i in self._batches:
            i.draw(self._shader)
        # gpu.matrix.get_normal_matrix()


draw = Draw()


class ZENU_OT_load_bsync(bpy.types.Operator):
    bl_label = 'BSync Load'
    bl_idname = 'zenu.load_bsync'

    def execute(self, context: bpy.types.Context):
        data = requests.get('http://127.0.0.1:8000/projects/test').json()
        positions = []
        draw.load_data(data)
        draw.load_frame_scene(context.scene)

        # for i in data['values']['_framesWidgets']['1']:
        #     for i in i['values']['_points']:
        #         positions.append(mathutils.Vector((i['x'], i['y'])))
        #     continue
        #
        # draw.update(positions)
        update_window(all_w=True)
        return {'FINISHED'}


class ZENU_PT_bsync(BasePanel):
    bl_label = 'bsync'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_load_bsync.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_bsync,
    ZENU_OT_load_bsync
))


@persistent
def frame_update(scene):
    draw.load_frame_scene(scene)


def register():
    reg()
    draw.register()
    space.register()
    bpy.app.handlers.frame_change_pre.append(frame_update)


def unregister():
    unreg()
    draw.unregister()
    space.unregister()
    bpy.app.handlers.frame_change_pre.remove(frame_update)

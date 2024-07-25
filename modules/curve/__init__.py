import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import bpy
import gpu
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
        "  FragColor = vec4(vec3(1, 1, 0), 1.0);"
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


class CurveDraw(GpuDrawer):
    draws: list[ShaderDraw]
    _point: ShaderDraw
    _points: list[Vector]

    def __init__(self):
        self.draws = []
        self.rebuild()
        self._point = ShaderDraw.from_shader({'position': create_sphere()}, create_shader(), type='LINES')
        self._points = []
        b = Beizer(
            p0=Vector((-5, 0, -1)),
            p1=Vector((-1, 0, 1)),
            p2=Vector((1, 0, 1)),
            p3=Vector((1, 0, -1))
        )

    def calc_beizer(self, beizer: Beizer, t: float) -> Vector:
        p0 = beizer.p0
        p1 = beizer.p1
        p2 = beizer.p2
        p3 = beizer.p3

        a = p0.lerp(p1, t)
        b = p1.lerp(p2, t)

        c = p2.lerp(p3, t)
        d = a.lerp(b, t)

        e = b.lerp(c, t)
        return d.lerp(e, t)

    def beizer_to_points(self, beizer: Beizer, quality: int = 40):
        points = []
        for i in range(0, quality + 1):
            points.append(self.calc_beizer(beizer, i / quality))
        return points

    def beizer_controllers(self, beizer: Beizer):
        coords = [beizer.p0, beizer.p1, beizer.p2, beizer.p3]
        return coords

    def rebuild(self):
        b = self.draws

        self.draws.clear()
        self.draws.append(ShaderDraw.from_builtin(coords=self.beizer_to_points(b), type='LINE_STRIP'))
        self.draws.append(ShaderDraw.from_builtin(coords=self.beizer_controllers(b), type='LINES'))

        self._points.clear()
        self._points.append(b.p0)
        self._points.append(b.p1)
        self._points.append(b.p2)
        self._points.append(b.p3)

    def draw(self):
        for i in self.draws:
            shad = i.shader
            shad.uniform_float('color', (1, 1, 1, 1))
            i.draw()

        shad = self._point.shader
        matrix = bpy.context.region_data.perspective_matrix
        shad.uniform_float("viewProjectionMatrix", matrix)

        for i in self._points:
            shad.uniform_float('size', .2)
            shad.uniform_float('offset', i)
            self._point.draw()


class ModalOperator(bpy.types.Operator):
    bl_idname = "zenu.edit_curve"
    bl_label = "Edit Curve"

    def __init__(self):
        pass

    def __del__(self):
        pass

    def execute(self, context):
        pass
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':  # Apply
            self.value = event.mouse_x
            self.execute(context)
        elif event.type == 'LEFTMOUSE':  # Confirm
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            # Revert all changes that have been made
            context.object.location.x = self.init_loc_x
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc_x = context.object.location.x
        self.value = event.mouse_x
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


curve = CurveDraw()


def update(self, scene):
    curve.rebuild()


class DrawTest(bpy.types.PropertyGroup):
    t: bpy.props.FloatProperty(default=0, min=0, max=1, update=update, subtype='FACTOR')


class ZENU_PT_curve(BasePanel):
    bl_label = 'Curve'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        layout.prop(context.scene.zenu_draw_test, 't')


reg, unreg = bpy.utils.register_classes_factory((
    DrawTest,
    ZENU_PT_curve
))


def register():
    reg()
    bpy.types.Scene.zenu_draw_test = bpy.props.PointerProperty(type=DrawTest)
    # curve.register()


def unregister():
    unreg()
    # curve.unregister()

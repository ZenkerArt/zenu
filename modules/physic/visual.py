import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Quaternion, Matrix
from .transform import ZTransforms
import bpy


class ZVisualShader:
    batch: gpu.types.GPUBatch = None
    shader: gpu.types.GPUShader = None
    _points: list[Vector]
    _colors: list

    def __init__(self):
        self.transforms = ZTransforms()
        self._points = []
        self._colors = []

    def add_point(self, x: float, y: float, z: float, color: Vector):
        self._points.append(Vector((x, y, z)))
        self._colors.append((*color, 1))

    def init(self):
        self.shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        self.batch = batch_for_shader(self.shader, 'LINES', {"pos": self.points, 'color': self._colors})

    def draw(self, obj: 'ZVisualObject'):
        matrix = bpy.context.region_data.perspective_matrix

        matrix = matrix @ obj.transforms.matrix_world

        self.shader.uniform_float("ModelViewProjectionMatrix", matrix)
        # self.shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        # self.shader.uniform_float("lineWidth", 4.5)
        # self.shader.uniform_float("color", (1, 1, 0, 1))
        self.batch.draw(self.shader)

    @property
    def points(self):
        return self._points


class ZVisualObject:
    transforms: ZTransforms
    shader: ZVisualShader

    def __init__(self, shader: ZVisualShader):
        self.transforms = ZTransforms()
        self.shader = shader


class ZVisualizer:
    _objects: dict[str, ZVisualObject]
    _xyz_shader: ZVisualShader
    handler = None

    def __init__(self):
        self._xyz_shader = ZVisualShader()
        self._xyz_shader.add_point(0, 0, 0, color=Vector((1, 0, 0)))
        self._xyz_shader.add_point(1, 0, 0, color=Vector((1, 0, 0)))

        self._xyz_shader.add_point(0, 0, 0, color=Vector((0, 1, 0)))
        self._xyz_shader.add_point(0, 1, 0, color=Vector((0, 1, 0)))

        self._xyz_shader.add_point(0, 0, 0, color=Vector((0, 0, 1)))
        self._xyz_shader.add_point(0, 0, 1, color=Vector((0, 0, 1)))
        self._xyz_shader.init()

        self._objects = {}

    @property
    def objects(self):
        return self._objects

    def get_xyz_point(self, name: str):
        obj = self._objects.get(name)
        if obj is not None:
            return obj

        obj = ZVisualObject(self._xyz_shader)
        self._objects[name] = obj
        return obj

    def draw(self):
        for obj in self._objects.values():
            obj.shader.draw(obj)

    def clear(self):
        self._objects.clear()

    def register(self):
        self.handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')

    def unregister(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')

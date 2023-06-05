import math
from typing import Any

import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


class Draw3D:
    _shader: Any = None

    def __init__(self):
        self._shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

    def draw_lines(self, coords: list[Vector], type: str = 'LINES', color=(1, 1, 1)):
        self._shader.uniform_float("color", (*color, 1))
        batch = batch_for_shader(self._shader, type, {"pos": coords})
        gpu.state.line_width_set(2)
        batch.draw(self._shader)

    def draw_circle(self, pos: Vector, start=0, end=math.pi * 2, radius: float = 1):
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

        self._shader.uniform_float("color", (1, 1, 0, 1))
        self.draw_lines(coords, type='LINE_STRIP')
        return Vector(coords[int(len(coords) / 2)])

import math

from mathutils import Vector
from .bezier import Bezier
from .draw_3d import Draw3D


def xy2xz(value: list):
    return Vector((value[0], 0, value[1]))


def bezier_draw(curve: Bezier, drawer: Draw3D, scale: float = 5, steps: int = 25):
    coords = []
    coords_comb = []
    coords_comb_line = []

    for i in range(0, steps + 1):
        t = i * (1 / steps)
        p = xy2xz(curve.position(t))
        coords.append(p)

    k = 0
    ka = 0
    count = 1
    for i in range(0, steps + 1):
        t = i * (1 / steps)
        c = curve.curvature(t)
        p = xy2xz(curve.position(t))
        n = xy2xz(curve.normal(t) * (c * -scale))
        pn = p + n

        coords_comb.append(pn)
        coords_comb_line.append(p)
        coords_comb_line.append(pn)

        k += c
        ka += math.fabs(c)
        count += 1

    color = (.26171875, .546875, .828125)
    drawer.draw_lines(coords, type='LINE_STRIP', color=(.82421875, .453125, .12109375))
    drawer.draw_lines(coords_comb, type='LINE_STRIP', color=color)
    drawer.draw_lines(coords_comb_line, color=(.7, .7, .7))

    return k, ka, count
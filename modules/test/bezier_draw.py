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
        count += 1

    drawer.draw_lines(coords, type='LINE_STRIP', color=(.8, .8, .8))
    drawer.draw_lines(coords_comb, type='LINE_STRIP', color=(1, 1, 1))
    drawer.draw_lines(coords_comb_line, color=(.5, .5, .5))

    return k, count
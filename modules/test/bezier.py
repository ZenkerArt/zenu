import numpy as np


def normal(point: np.ndarray):
    return np.array((-point[1], point[0]))


def mag(point: np.ndarray):
    return np.sqrt(np.sum(point ** 2))


def normalise(point: np.ndarray):
    return point * 1 / mag(point)


def lerp(p1: np.ndarray, p2: np.ndarray, t: float):
    return p1 * (1 - t) + p2 * t


class Bezier:
    p0: np.ndarray
    p1: np.ndarray
    p2: np.ndarray
    p3: np.ndarray

    def __init__(self, p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

    def _find_tangent(self, t: float):
        b1 = (self.p1 - self.p0) * 3 * (1 - t) ** 2
        b2 = (self.p2 - self.p1) * 6 * (1 - t) * t
        b3 = (self.p3 - self.p2) * 3 * t ** 2
        return b1 + b2 + b3

    def _dd(self, t: float):
        return 6 * (1 - t) * (self.p2 - 2 * self.p1 + self.p0) + 6 * t * (self.p3 - 2 * self.p2 + self.p1)

    def position(self, t: float):
        b0 = self.p0 * (1 - t) ** 3
        b1 = self.p1 * 3 * (1 - t) ** 2 * t
        b2 = self.p2 * 3 * (1 - t) * t ** 2
        b3 = self.p3 * t ** 3
        return b0 + b1 + b2 + b3

    def tangent(self, t: float):
        return normalise(self._find_tangent(t))

    def normal(self, t: float):
        return normalise(normal(self.tangent(t)))

    def curvature(self, t: float) -> float:
        tx, ty = self._find_tangent(t)
        dx, dy = self._dd(t)
        return (tx * dy - ty * dx) / (tx ** 2 + ty ** 2) ** (3 / 2)

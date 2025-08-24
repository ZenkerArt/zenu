import math

from mathutils import Quaternion, Vector


class ZAngularSolverSettings:
    stiffness: float = 100
    damping: float = 10


class ZAngularSolver:
    settings: ZAngularSolverSettings
    delta_time: float = 1 / 60

    def __init__(self):
        self.settings = ZAngularSolverSettings()

    def solve(self, q_current: Quaternion, q_target: Quaternion, angular_velocity: Vector):
        stiffness, damping, dt = self.settings.stiffness, self.settings.damping, self.delta_time

        if q_current.dot(q_target) < 0.0:
            q_target = -q_target

        q_delta = q_target @ q_current.conjugated()
        angle = q_delta.angle
        axis = q_delta.axis
        angular_velocity += axis * angle * stiffness * dt
        angular_velocity *= math.exp(-damping * dt)

        speed = angular_velocity.length

        if speed > 1e-8:
            axis_norm = angular_velocity / speed
            q_step = Quaternion(axis_norm, speed * dt)
            q_current = q_step @ q_current

        return q_current, angular_velocity
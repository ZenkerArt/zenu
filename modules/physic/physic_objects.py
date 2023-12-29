from abc import ABC, abstractmethod

import bpy
from mathutils import Vector
from mathutils.noise import random


def distance_vec(point1: Vector, point2: Vector) -> float:
    return (point2 - point1).length


class PhysicObject(ABC):
    @abstractmethod
    def update(self):
        pass


class PhysicHandler:
    _objects: list[PhysicObject]
    _is_enable: bool = False

    def __init__(self):
        self._objects = []

    def add_object(self, obj: PhysicObject):
        self._objects.append(obj)

    def update(self, scene, _):
        if not self._is_enable: return

        for i in self._objects:
            i.update()

    def clear(self):
        self._objects.clear()

    def start(self):
        if not self._is_enable:
            bpy.app.handlers.frame_change_pre.append(self.update)
        self._is_enable = True

    def stop(self):
        try:
            bpy.app.handlers.frame_change_pre.remove(self.update)
        except Exception:
            pass

        self._is_enable = False

    def toggle(self):
        if self._is_enable:
            self.stop()
        else:
            self.start()

    def is_enable(self):
        return self._is_enable


class Noise(PhysicObject):
    def __init__(self, obj: bpy.types.Object):
        self.obj = obj
        self.noise_pos = Vector((0, 0, 0))

    def update(self):
        frame = bpy.context.scene.frame_current
        fps = bpy.context.scene.render.fps
        seconds = frame / fps

        noise_strange = 0
        noise_rate = 1
        noise_enable = False

        try:
            noise_enable = self.obj.follow_settings.noise_enable
            noise_strange = self.obj.follow_settings.noise_strange
            noise_rate = 1 - self.obj.follow_settings.noise_rate
            coords = Vector(self.obj.follow_settings.noise_coords)
        except Exception:
            pass

        rate = int(fps * noise_rate)

        if noise_enable and rate == 0 or (frame % rate) == 1:
            self.noise_pos = (Vector((.5 - random(), .5 - random(), .5 - random())) * noise_strange) * coords


class FollowObject(PhysicObject):
    target: bpy.types.PoseBone
    obj: bpy.types.Object
    velocity: Vector
    noise: Noise
    loc: Vector
    dist: float

    def __init__(self, target: bpy.types.PoseBone, obj: bpy.types.Object):
        self.target = target
        self.obj = obj
        self.velocity = Vector((0, 0, 0))
        self.noise = Noise(obj)
        self.loc = Vector((0, 0, 0))
        self.dist = 0

    def update(self):
        target_loc = (self.target.matrix @ self.target.location.copy()).xzy

        speed = .2
        velocity = .2
        noise_enable = False
        only_velocity = False

        try:
            speed = self.obj.follow_settings.speed
            velocity = 1 - self.obj.follow_settings.velocity
            noise_enable = self.obj.follow_settings.noise_enable
            only_velocity = self.obj.follow_settings.only_velocity
        except Exception:
            pass

        self.velocity *= velocity

        if noise_enable:
            self.noise.update()
            target_loc += self.noise.noise_pos

        self.velocity += (target_loc - self.loc) * speed
        self.loc += self.velocity

        if only_velocity:
            self.obj.location = self.velocity * -1
        else:
            self.obj.location = self.loc

        # self.loc *= .5

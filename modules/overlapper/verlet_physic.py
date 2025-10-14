import math
from mathutils import Matrix, Quaternion, Vector
EPS = 1e-8


def get_angle(a, b, c):
    u = (a - b).normalized()
    v = (c - b).normalized()
    return math.acos(max(-1.0, min(1.0, u.dot(v))))


class VerletObject:
    mat: Matrix
    location: Vector
    rot: Quaternion
    old_location: Vector
    rest: float = 0
    index: int

    def __init__(self):
        self.mat = Matrix()
        self.location = Vector()
        self.rot = Quaternion()
        self.rest_angle = Vector()
        self.old_location = Vector()
        self.index = -1


class AngleConstraint:
    p1: VerletObject
    p2: VerletObject
    p3: VerletObject
    rest_angle: float

    def __init__(self, p1: VerletObject, p2: VerletObject, p3: VerletObject):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        # self.rest_angle = get_angle(p1.location, p2.location, p3.location)
        self.rest_angle = math.pi / 2

    def apply(self, stiffness=.2):
        a = self.p1.location
        b = self.p2.location

        diff = a - b
        rot = self.p1.mat.to_quaternion() @ diff.normalized().rotation_difference(Vector((math.pi, 0, 0)))
        # rot.

        self.p2.rot = rot
        self.p2.location += rot @ diff * (1 - self.p2.index / 10) * .05


class VerletPhysic:
    _objects: list[VerletObject]
    _angle_constraints: list[AngleConstraint]

    def __init__(self):
        self._objects = []
        self._angle_constraints = []
        leng = 1
        obj_count = 10
        for i in range(obj_count):
            obj = VerletObject()
            obj.location.z = leng * i
            obj.rest = leng
            obj.index = i

            self._objects.append(obj)

        for i in range(obj_count - 1):
            self._angle_constraints.append(AngleConstraint(
                self._objects[i], self._objects[i+1], self._objects[i]))

    @property
    def objects(self):
        return self._objects

    def update(self) -> None:
        dt = 1/60
        gravity = Vector((0, 0, -1))

        for i, ob in enumerate(self._objects):
            if i == 0:
                continue
            velocity = (ob.location - ob.old_location) * .98
            ob.old_location = ob.location.copy()

            ob.location += velocity
            ob.location += gravity * dt

        for step in range(100):
            for i in range(len(self.objects) - 1):

                obj = self._objects[i]
                obj_next = self._objects[i + 1]

                pos_diff = obj.location - obj_next.location

                dist = pos_diff.length
                diff = dist - obj.rest

                change_dir = pos_diff.normalized()
                change_vector = change_dir * diff

                if (i != 0):
                    obj.location -= change_vector * .5
                    obj_next.location += change_vector * .5
                else:
                    obj_next.location += change_vector * .1

        for i in self._angle_constraints:
            i.apply()
        # for step in range(100):
        #     for i in range(len(self.objects) - 1):

        #         obj = self._objects[i]
        #         obj_next = self._objects[i + 1]

        #         diff = obj_next.location - obj.location
        #         dist = diff.length

        #         if dist < .0001: continue

        #         delta_dist = (dist - obj.rest) / dist
        #         correction = 0.5 * diff * delta_dist

        #         if i != 0:
        #             obj.location += correction
        #         obj_next.location -= correction

        #         # n = diff.normalized()
        #         # velocity_diff = obj_next.velocity - obj.velocity

        #         # vn = n * velocity_diff.dot(n)
        #         # # print(n, velocity_diff)
        #         # # if i != 0:
        #         # # print(velocity_diff.dot(n) )
        #         # obj.velocity += 0.5 * vn
        #         # obj_next.velocity -= 0.5 * vn

        # for i in range(len(self.objects) - 1):
        #     obj = self._objects[i]
        #     obj_next = self._objects[i + 1]

        #     diff = obj_next.location - obj.location
        #     dist = diff.length

        #     if dist < .0001: continue

        #     n = diff.normalized()
        #     velocity_diff = obj_next.velocity - obj.velocity

        #     vn = n * velocity_diff.dot(n)
        #     # print(n, velocity_diff)
        #     # if i != 0:
        #     print(velocity_diff.dot(n) )
        #     obj.velocity += 0.5 * vn
        #     obj_next.velocity -= 0.5 * vn

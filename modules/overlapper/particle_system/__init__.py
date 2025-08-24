import math
from mathutils import Matrix, Vector, Quaternion


class ParticleTransform:
    _loc: Vector
    _rot: Quaternion
    _scale: Vector

    def __init__(self):
        self._loc = Vector()
        self._rot = Quaternion()
        self._scale = Vector((1, 1, 1))

    @property
    def location(self):
        return self._loc

    @location.setter
    def location(self, value: Vector):
        self._loc = value

    @property
    def rotation(self):
        return self._rot

    @rotation.setter
    def rotation(self, value: Quaternion):
        self._rot = value

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value: Vector):
        self._scale = value

    @property
    def matrix(self):
        mat = Matrix.LocRotScale(self.location, self.rotation, self.scale)

        return mat

    @matrix.setter
    def matrix(self, value: Matrix):
        self._loc, self._rot, self._scale = value.decompose()


class Particle:
    transform: ParticleTransform
    velocity: Vector
    mass: float = 1

    def __init__(self):
        self.transform = ParticleTransform()
        self.velocity = Vector((0, 0, 0))


class ParticleConstraint:
    _part1: Particle
    _part2: Particle
    _diff: Vector
    _dist: Vector

    def __init__(self, part1: Particle, part2: Particle):
        self._part1 = part1
        self._part2 = part2

    def simple(self):
        t1, t2 = self._part1.transform, self._part2.transform
        v1, v2 = self._part1.velocity, self._part2.velocity
        m1, m2 = self._part1.mass, self._part2.mass

        diff = t1.location - t2.location
        dist = diff.length

        k = .2

        invM1, invM2 = 1.0/m1, 1.0/m2
        m_eff = 1.0 / (invM1 + invM2)
        c_crit = 2.0 * math.sqrt(k * m_eff)
        c = 1.0 * c_crit

        # print(dist)

        n = diff / dist
        ext = dist - .4

        v_rel = v1 - v2
        v_rel_n = v_rel.dot(n)

        Fspring = k * ext * n
        Fdamp = c * v_rel_n * n

        F = Fspring + Fdamp
        self._part1.velocity -= F
        self._part2.velocity += F

    def update(self, delta: float):
        self.simple()
        # t1, t2 = self._part1.transform, self._part2.transform
        # v1, v2 = self._part1.velocity, self._part2.velocity
        # m1, m2 = self._part1.mass, self._part2.mass

        # dt = 0.01
        # L = 1.0

        # beta = 0.02

        # diff = t2.location - t1.location
        # dist = diff.length

        # n = diff / dist
        # C = dist - L
        # w = invM1 + invM2

        # dp = -(C / w) * n

        # t1.location -= invM1 * dp
        # t2.location += invM2 * dp

        # v_rel = v1 - v2
        # v_rel_n = v_rel.dot(n)

        # v_target_n = -beta * C / dt
        # j = - (v_rel_n - v_target_n) / w
        # impulse = j * n
        # print(impulse)
        # self._part1.velocity -= invM1 * impulse
        # self._part2.velocity += invM2 * impulse


class ParticleSystem:
    _particles: list[Particle]
    _constraints: list[ParticleConstraint]
    _dumping: float = 2

    def __init__(self):
        self._particles = []
        self._constraints = []

    def _velocity_solver(self, particle: Particle, delta: float):
        particle.transform.location += particle.velocity
        particle.velocity -= Vector((0, 0, .005)) * particle.mass
        particle.velocity *= math.exp(-self._dumping * delta)

    def add_particle(self):
        particle = Particle()

        self._particles.append(particle)

        return particle

    def add_constraint(self, part1: Particle, part2: Particle):
        self._constraints.append(ParticleConstraint(part1, part2))

    @property
    def particles(self) -> list[Particle]:
        return self._particles

    def update(self, delta: float = 1):
        print('Start'.center(20, '-'))
        for particle in self._particles:
            self._velocity_solver(particle, delta)

        for const in self._constraints:
            const.update(delta)

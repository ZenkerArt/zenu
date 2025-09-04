

from collections import defaultdict
from dataclasses import dataclass, field

from mathutils import Matrix, Quaternion, Vector
from .overlapper_settings import OverlapperSettings
from .angular_solver import ZAngularSolver
from .transform_baker import BoneRecord, TransformBaker


@dataclass
class MotionVector:
    force: Vector
    vector: Vector
    speed: float


@dataclass
class RotationBasedOverlapperData:
    rotation_velocity: Quaternion = field(default_factory=Quaternion)
    angular_velocity: Vector = field(default_factory=Vector)
    offset: Matrix = field(default_factory=Matrix)
    rot_offset: Matrix = field(default_factory=Matrix)


class RotationBasedOverlapper:
    _baker: TransformBaker
    _angular_solver: ZAngularSolver
    _settings: OverlapperSettings

    def __init__(self, baker: TransformBaker, settings: OverlapperSettings):
        self._baker = baker
        self._angular_solver = ZAngularSolver()
        self._angular_solver.settings.damping = settings.damping
        self._angular_solver.settings.stiffness = settings.stiffness
        self._settings = settings

    def calculate_motion(self, settings: 'OverlapperSettings', frame: int, bone: BoneRecord, first_bone: BoneRecord):
        try:
            motion_bone = bone

            if settings.only_root_motion:
                motion_bone = first_bone

            next_frame = motion_bone.get_frame(frame + 1)
            motion_vec = motion_bone.get_frame(frame).matrix_result.to_translation(
            ) - next_frame.matrix_result.to_translation()
            motion_speed = motion_vec.length * settings.motion_multiply
        except KeyError:
            motion_vec = Vector()
            motion_speed = 0

        return MotionVector(
            force=motion_vec,
            vector=motion_vec.normalized(),
            speed=motion_speed
        )

    def bone_rest_matrix(self, bone: BoneRecord):
        for frame in self._baker.get_range_offset():
            transform = bone.get_frame(frame)
            transform.matrix_result = transform.matrix_world

    def calc(self):
        baker = self._baker
        # add_empty()

        ov_data: dict[str, RotationBasedOverlapperData] = defaultdict(
            RotationBasedOverlapperData)
        settings = self._settings
        bones = baker.get_bone_records()
        start_frame = baker.start_offset
        first_bone = bones[0][1]

        for name, bone in bones:
            self.bone_rest_matrix(bone)

            if bone.parent is None:
                continue

            loc, rot, _ = bone.parent.get_frame(
                start_frame).matrix_world.decompose()
            mat1 = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))

            loc, rot, _ = bone.get_frame(start_frame).matrix_world.decompose()
            mat2 = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))

            ov_data[name].offset = (mat1.inverted() @ mat2)

        for name, bone in bones:
            ov_data[name].rotation_velocity = bone.get_frame(baker.start_offset)\
                .matrix_world.to_quaternion()

            for frame in self._baker.get_range_offset():
                if bone.parent is None:
                    continue

                data = ov_data[name]
                transform_parent = bone.parent.get_frame(frame)
                transform = bone.get_frame(frame)

                motion = self.calculate_motion(
                    settings,
                    frame,
                    bone,
                    first_bone
                )

                mat: Matrix = transform_parent.matrix_result @ data.offset

                base_vec: Vector = mat.col[1].to_3d().normalized()

                rot_quat = base_vec.rotation_difference(motion.vector)

                wind = base_vec.rotation_difference(
                    Vector(settings.wind)
                    + mat.col[1].to_3d().normalized()
                )

                data.angular_velocity += Vector(rot_quat.to_euler())\
                    * motion.speed\
                    * settings.motion_multiply

                data.angular_velocity += Vector(wind.to_euler())

                target_rotation = mat\
                    .to_quaternion() @\
                    (bone.child.get_frame(frame).matrix_basis.to_quaternion().conjugated() 
                     @ bone.child.get_frame(start_frame).matrix_basis.to_quaternion())

                data.rotation_velocity, data.angular_velocity = self._angular_solver.solve(
                    data.rotation_velocity,
                    target_rotation,
                    data.angular_velocity
                )

                transform.matrix_result = Matrix.LocRotScale(
                    mat.to_translation(),
                    data.rotation_velocity,
                    None
                )

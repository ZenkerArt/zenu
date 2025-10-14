import bpy
from .transform_baker import ConstraintCreator, TransformBaker
from .angular_solver import ZAngularSolver
from .visual import OvVisualizer
from .verlet_physic import VerletPhysic


class OvContext:
    visual: OvVisualizer
    baker: TransformBaker
    angular_solver: ZAngularSolver
    verlet_physic: VerletPhysic

    def __init__(self):
        self.visual = OvVisualizer()
        self.baker = TransformBaker()
        self.constraints = ConstraintCreator(self.baker)
        self.angular_solver = ZAngularSolver()
        self.verlet_physic = VerletPhysic()

    @property
    def settings(self) -> 'OverlapperSettings':
        return bpy.context.scene.ov_settings


ov_context = OvContext()

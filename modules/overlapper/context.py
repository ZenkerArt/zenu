import bpy
from .transform_baker import ConstraintCreator, TransformBaker
from .angular_solver import ZAngularSolver
from .visual import OvVisualizer


class OvContext:
    visual: OvVisualizer
    baker: TransformBaker
    angular_solver: ZAngularSolver

    def __init__(self):
        self.visual = OvVisualizer()
        self.baker = TransformBaker()
        self.constraints = ConstraintCreator(self.baker)
        self.angular_solver = ZAngularSolver()

    @property
    def settings(self) -> 'OverlapperSettings':
        return bpy.context.scene.ov_settings

ov_context = OvContext()
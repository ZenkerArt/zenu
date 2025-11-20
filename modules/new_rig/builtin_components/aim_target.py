from typing import Any
import bpy
from ..layers import BoneCollectorLayer, CopyConstraintLayer, RigComponentsLayer, StyleLayer, BoneCollectionLayer
from ..rig_lib import RigComponent, RigContext
from ..rig_lib.bone_utils import bone_clone


class AimTarget(RigComponent):
    name = 'Aim Target'

    def __init__(self):
        super().__init__()

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        pass

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, layers: RigComponentsLayer):
        pass

    def execute_pose(self, context: RigContext, bones_collector: BoneCollectorLayer):
        pass

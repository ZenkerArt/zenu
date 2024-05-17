from dataclasses import dataclass

import bpy
from .. import FunctionNodeResult, FunctionNode


@dataclass
class SceneInfo(FunctionNodeResult):
    frame: float


class ZENU_ND_scene_info(FunctionNode):
    bl_label = 'Scene Info'

    def call(self) -> SceneInfo:
        return SceneInfo(
            frame=float(bpy.context.scene.frame_current)
        )


nodes = (
    ZENU_ND_scene_info,
)

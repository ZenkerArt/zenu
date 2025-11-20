from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Type, TypeVar

import bpy

from ..rig_lib import RigBone, RigLayer, RigComponent, RigContext
T = TypeVar('T')


@dataclass
class BoneStyle:
    bone: RigBone
    shape: str


class StyleLayer(RigLayer):
    _bones: list[BoneStyle]

    def __init__(self):
        super().__init__()
        self._bones = []

    def apply_shape(self, bone: RigBone, shape: str):
        self._bones.append(BoneStyle(
            bone=bone,
            shape=shape
        ))

    def execute(self, context: RigContext):
        bpy.ops.object.mode_set(mode='POSE')
        shapes = defaultdict(list)

        for style in self._bones:

            shape_name = style.shape

            if not shape_name:
                continue

            shapes[shape_name].append(style.bone.name)

        for obj, bones in shapes.items():
            for b in bones:
                context.new_armature.pose.bones[b].custom_shape = obj

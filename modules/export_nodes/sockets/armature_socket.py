from dataclasses import dataclass

import bpy

from .base import BaseSocketType, base_draw

@dataclass
class ArmatureSocketResponse:
    armature: bpy.types.Object
    action_slot_name: str

class ArmatureTypeSocket(BaseSocketType):
    Response = ArmatureSocketResponse
    bl_idname = "ArmatureTypeSocket"
    bl_label = "Armature"

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.1, 1.0)


reg, unreg = bpy.utils.register_classes_factory((ArmatureTypeSocket,))


def register():
    reg()


def unregister():
    unreg()

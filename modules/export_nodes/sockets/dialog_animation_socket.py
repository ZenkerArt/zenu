from dataclasses import dataclass

import bpy

from .base import BaseSocketType, base_draw

@dataclass
class DialogAnimationSocketResponse:
    action: bpy.types.Action
    sound: str = None

class DialogAnimationTypeSocket(BaseSocketType):
    Response = DialogAnimationSocketResponse

    bl_idname = "DialogAnimationTypeSocket"
    bl_label = "Dialog Animation"

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.1, 1.0)


reg, unreg = bpy.utils.register_classes_factory((DialogAnimationTypeSocket,))


def register():
    reg()


def unregister():
    unreg()

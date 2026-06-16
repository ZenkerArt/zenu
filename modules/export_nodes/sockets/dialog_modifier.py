from typing import Any

import bpy

from .base import BaseSocketType, base_draw

class DialogModifier:
    def execute(self):
        return

class DialogModifierStack:
    _modifiers: list[DialogModifier]

    def __init__(self):
        self._modifiers = []

    def add_mod(self, data: DialogModifier):
        self._modifiers.append(data)

    @property
    def modifiers(self):
        return self._modifiers


class DialogModifierSocketType(BaseSocketType):
    Response = DialogModifierStack

    bl_idname = "DialogSocketType"
    bl_label = "Dialog Modifier"
    value = None

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.2, 0.4, 0.8, 1.0)


reg, unreg = bpy.utils.register_classes_factory((
    DialogModifierSocketType,
))


def register():
    reg()


def unregister():
    unreg()

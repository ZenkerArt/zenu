from typing import Any

import bpy

from .base import BaseSocketType, base_draw


class FileExportPromise:
    def export(self, path: str, root: str) -> list[str]:
        pass


class FileSocketType(BaseSocketType):
    bl_idname = "FileSocketType"
    bl_label = "File"
    map_type = FileExportPromise
    value = None

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.2, 0.4, 0.8, 1.0)


reg, unreg = bpy.utils.register_classes_factory((
    FileSocketType,
))


def register():
    reg()


def unregister():
    unreg()

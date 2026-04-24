from . import BaseSocketType
import bpy


class FileSocketType(BaseSocketType):
    bl_idname = "FileSocketType"
    bl_label = "File"

    def draw(self, context, layout, node, text):
        layout.prop(self, "value", text=text)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.2, 1.0)

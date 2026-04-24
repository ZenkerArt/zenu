import bpy
from .base_node import BaseNode
from .. import node_categories


class ExportConfig(BaseNode):
    bl_idname = "ExportConfig"
    bl_label = "Export Config"

    def draw_buttons(self, context, layout):
        pass

    def init(self, context):
        self.inputs.new()


reg, unreg = bpy.utils.register_classes_factory((
    ExportConfig,
))


def register():
    node_categories.general.add_node(ExportConfig)
    reg()


def unregister():
    unreg()

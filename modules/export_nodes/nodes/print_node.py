from dataclasses import dataclass
from typing import Any
from pprint import pprint, pformat

import bpy

from .base_node import SimpleNode
from .. import node_categories


@dataclass
class PrintOutputs:
    object: Any

    def get(self, name: str):
        return getattr(self, name)


class PrintNode(SimpleNode):
    bl_idname = "PrintNode"
    bl_label = "Print"
    data: bpy.props.StringProperty(default="")

    def draw_buttons(self, context, layout):
        for line in self.data.split('\n'):
            layout.label(text=line)

    def compute(self, object: Any) -> PrintOutputs:
        formatted = pformat(object, indent=4, width=80)
        self.data = formatted
        return PrintOutputs(object=object)


reg, unreg = bpy.utils.register_classes_factory((
    PrintNode,
))


def register():
    reg()
    node_categories.general.add_node(PrintNode)


def unregister():
    unreg()

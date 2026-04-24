from typing import Any

import bpy

from .base_node import BaseNode
from .. import node_categories
from ..sockets import ObjectSocketType


class ObjectNode(BaseNode):
    bl_idname = "ObjectNode"
    bl_label = "Object"

    # bl_icon = 'INFO'

    def compute(self) -> dict[str, Any]:
        return {
            'obj': self.outputs['obj'].value
        }

    def init(self, context):
        self.outputs.new(ObjectSocketType.bl_idname, "obj")


reg, unreg = bpy.utils.register_classes_factory((
    ObjectNode,
))


def register():
    reg()
    node_categories.general.add_node(ObjectNode)


def unregister():
    unreg()


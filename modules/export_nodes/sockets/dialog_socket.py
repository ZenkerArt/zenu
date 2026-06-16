from collections import defaultdict
from typing import Any

import bpy

from .base import BaseSocketType, base_draw
from ..nodes import BaseNode


class ZENU_OT_remove_dialog_socket(bpy.types.Operator):
    bl_label = 'Remove Dialog Socket'
    bl_idname = 'zenu.remove_dialog_socket'

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}


class DialogContext:
    context: dict[str, Any]
    nodes: set[BaseNode]
    forward_links: dict[BaseNode, set[BaseNode]]
    backward_links: dict[BaseNode, set[BaseNode]]

    def __init__(self):
        self.forward_links = defaultdict(set)
        self.backward_links = defaultdict(set)
        self.nodes = set()
        self.context = defaultdict(dict)

    def add_link(self, frm: BaseNode, to: BaseNode):
        self.forward_links[frm].add(to)
        self.backward_links[to].add(frm)

        self.nodes.add(frm)
        self.nodes.add(to)

    def get_store(self, node: BaseNode):
        return self.context[node]

    @staticmethod
    def node_name(self):
        return getattr(self, "name", str(self))

    def print_graph(self):
        for node in self.nodes:
            outs = self.forward_links.get(node, [])
            ins = self.backward_links.get(node, [])

            print(f"[{self.node_name(node)}]")
            print(f"  → {', '.join(self.node_name(n) for n in outs) or '∅'}")
            print(f"  ← {', '.join(self.node_name(n) for n in ins) or '∅'}")
            print()

    @staticmethod
    def print_tree(ctx, start_node, depth=0, visited=None):
        if visited is None:
            visited = set()

        indent = "  " * depth
        name = getattr(start_node, "name", str(start_node))

        print(f"{indent}- {name}")

        if start_node in visited:
            print(f"{indent}  (loop)")
            return

        visited.add(start_node)

        for nxt in ctx.forward_links.get(start_node, []):
            DialogContext.print_tree(ctx, nxt, depth + 1, visited.copy())


class DialogSocketType(BaseSocketType):
    bl_idname = "DialogSocketType"
    bl_label = "Dialog"
    map_type = DialogContext
    value = None

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.2, 0.4, 0.8, 1.0)


reg, unreg = bpy.utils.register_classes_factory((
    DialogSocketType,
    ZENU_OT_remove_dialog_socket
))


def register():
    reg()


def unregister():
    unreg()

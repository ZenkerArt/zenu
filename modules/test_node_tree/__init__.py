import inspect
from dataclasses import dataclass, field, asdict
from typing import Any

import bpy
import nodeitems_utils
from bpy.app.handlers import persistent
from bpy.types import NodeSocket
from mathutils import Vector
from .node_store import socket_store
from .property_node import PropertyNode
from ...utils import update_window
from .base_node import BaseNode, NodeContext
from .function_node import FunctionNodeResult, FunctionNode
from .node_tree import TestNodeTree
from .nodes import node_store
from .nodes.default_nodes import ZENU_ND_execute_node


class NodeBranchType:
    UNKNOWN = 'UNKNOWN'
    ROOT = 'ROOT'
    EXECUTABLE = 'EXECUTABLE'
    CONSTANT = 'CONSTANT'


@dataclass
class NodeBranch:
    value: Any
    parent_token: 'NodeBranch' = None
    from_connected: str = ''
    props: dict[str, 'NodeBranch'] = field(default_factory=dict)
    name: str = NodeBranchType.UNKNOWN

    def __repr__(self):
        val = self.value

        if inspect.isclass(type(val)):
            val = type(val).__name__

        return f'<NodeToken value="{val}" type="{self.name}">'


class NodeSystem:
    _node_tree: TestNodeTree

    def __init__(self, node: TestNodeTree):
        self._node_tree = node

    def _iter_node_tree(self, start_node: BaseNode, token: NodeBranch = None):
        if token is None:
            token = NodeBranch(start_node)

        link: bpy.types.NodeLink

        for inp in start_node.inputs:
            has_link = False

            for link in inp.links:
                has_link = True

                tok = self._iter_node_tree(link.from_node)
                tok.name = NodeBranchType.EXECUTABLE
                tok.parent_token = token
                tok.from_connected = link.from_socket.name
                token.props[inp.name] = tok

            if not has_link:
                value = inp.default_value
                tok = NodeBranch(value)
                tok.name = NodeBranchType.CONSTANT

                if isinstance(inp, bpy.types.NodeSocketVector):
                    tok.name = NodeBranchType.CONSTANT
                    tok.value = Vector(value)

                if tok.name != NodeBranchType.UNKNOWN:
                    token.props[inp.name] = tok

        return token

    def _execute_tree(self, node_branch: NodeBranch, context: bpy.types.Context, node_context: NodeContext):
        cache = node_context.node_cache

        if node_branch.name == NodeBranchType.ROOT:
            return self._execute_tree(node_branch.props['B'], context, node_context)

        if node_branch.name == NodeBranchType.CONSTANT:
            return node_branch.value

        if node_branch.name == NodeBranchType.EXECUTABLE:
            v = node_branch.value
            # v.node_tree = self._node_tree

            if isinstance(node_branch.value, FunctionNode):
                func = node_branch.value
                dct = {}

                for key, branch in node_branch.props.items():
                    val = self._execute_tree(branch, context, node_context)

                    if isinstance(val, FunctionNodeResult):
                        val = val.__dict__[branch.from_connected]

                    dct[key] = val

                node_context.props = dct
                value = cache.get(func.prop_id())
                try:
                    if value is None:
                        value = node_branch.value.execute(context, node_context)
                        cache.set(func.prop_id(), value)
                except Exception as e:
                    raise RuntimeError('Node Error', node_branch.value.name, e)

                return value

            if isinstance(node_branch.value, PropertyNode):
                return node_branch.value.execute(context, node_context)
                # cache.set('position', Vector())
                # cache.set(prop.prop_id(), prop.execute(context, node_context))

    def execute(self, context: bpy.types.Context):
        root_token = NodeBranch(None)
        root_token.name = NodeBranchType.ROOT
        for node in self._node_tree.nodes:
            if isinstance(node, ZENU_ND_execute_node):
                root_token.value = node
                self._iter_node_tree(node, root_token)
                break

        node_context = NodeContext({}, self._node_tree)
        self._execute_tree(root_token, context, node_context)


class ZENU_OT_execute_node_system(bpy.types.Operator):
    bl_label = 'Execute Node System'
    bl_idname = 'zenu.execute_node_system'

    def execute(self, context: bpy.types.Context):
        node_tree: TestNodeTree = context.space_data.edit_tree
        NodeSystem(node_tree).execute(context)
        update_window()
        return {'FINISHED'}


def draw(self, context: bpy.types.Context):
    if not isinstance(context.space_data.edit_tree, TestNodeTree):
        return

    layout: bpy.types.UILayout = self.layout
    layout.operator(ZENU_OT_execute_node_system.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    TestNodeTree,
    ZENU_OT_execute_node_system,
    *node_store.get_classes(),
    *socket_store.get_classes()
))

@persistent
def frame_update(scene):
    test_node_tree = bpy.data.node_groups.get('Test Node')
    if test_node_tree is not None:
        node_tree = bpy.data.node_groups['Test Node']
    NodeSystem(node_tree).execute(bpy.context)


def register():
    reg()
    nodeitems_utils.register_node_categories('CUSTOM', node_store.generate_nodes())
    bpy.types.NODE_HT_header.append(draw)
    bpy.app.handlers.frame_change_post.append(frame_update)


def unregister():
    unreg()
    nodeitems_utils.unregister_node_categories('CUSTOM')
    bpy.types.NODE_HT_header.remove(draw)
    bpy.app.handlers.frame_change_post.remove(frame_update)

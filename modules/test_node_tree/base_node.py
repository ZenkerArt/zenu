from abc import ABC
from dataclasses import dataclass, field
from typing import Any

import bpy
from .node_tree import TestNodeTree


class NodeCache:
    _cache: dict[str, Any]

    def __init__(self):
        self._cache = {}

    def get(self, name: str):
        return self._cache.get(name, None)

    def set(self, name: str, value: str):
        self._cache[name] = value

    def get_or_set(self, name: str, value: Any = None):
        v = self.get(name)

        if v is None:
            self.set(name, value)
            return value

        return v

    def get_dct(self):
        return self._cache


@dataclass
class NodeContext:
    props: dict[str, Any]
    node_tree: TestNodeTree
    attributes: dict[str, Any] = field(default_factory=dict)
    variables: NodeCache = field(default_factory=NodeCache)
    node_cache: NodeCache = field(default_factory=NodeCache)


class BaseNode(bpy.types.Node):
    def init(self, context: bpy.types.Context):
        pass

    def prop_id(self):
        return abs(hash(self.name) >> 50)

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == TestNodeTree.bl_idname

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        pass

    def execute(self, context: bpy.types.Context, node_context: NodeContext):
        pass

    def output(self, typ: str, name: str):
        return self.outputs.new(typ, name)

    def input(self, typ: str, name: str):
        inp = self.inputs.new(typ, name)

        return inp


class BaseVariableNode(BaseNode):
    pass

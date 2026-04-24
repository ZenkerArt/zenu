import bpy
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories
from hashlib import sha1


class ExportNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "ExportNodeTree"


class NodeCategory:
    _name: str
    _nodes: set[bpy.types.Node]

    def __init__(self, name: str):
        self._name = name
        self._nodes = set()

    def add_node(self, node: bpy.types.Node):
        self._nodes.add(node)

    def register(self):
        cat_id = sha1(self._name.encode()).hexdigest()
        node_categories = [
            ExportNodeCategory(cat_id, self._name,
                               items=[NodeItem(node.bl_idname) for node in self._nodes])
        ]
        register_node_categories(cat_id, node_categories)

    def unregister(self):
        unregister_node_categories(sha1(self._name.encode()).hexdigest())

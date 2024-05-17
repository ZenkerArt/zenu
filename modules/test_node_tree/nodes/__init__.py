import bpy.types
from mathutils import Vector
from ..node_store import node_store, socket_store, ZenuSocket
from . import \
    math_nodes, \
    default_nodes, \
    bone_nodes, \
    vector_math, \
    scene_nodes, \
    variable_nodes


def register_nodes(name: str, module):
    if hasattr(module, 'nodes'):
        node_store.add_nodes(name, module.nodes)

    if hasattr(module, 'sockets'):
        socket_store.add_sockets(module.sockets)


socket_store.add_sockets((
    ZenuSocket(
        socket=bpy.types.NodeSocketInt,
        types=(int,),
        register=False
    ),
    ZenuSocket(
        socket=bpy.types.NodeSocketFloat,
        types=(float,),
        register=False
    ),
    ZenuSocket(
        socket=bpy.types.NodeSocketString,
        types=(str,),
        register=False
    ),
    ZenuSocket(
        socket=bpy.types.NodeSocketBool,
        types=(bool,),
        register=False
    ),
    ZenuSocket(
        socket=bpy.types.NodeSocketVector,
        types=(Vector,),
        register=False
    ),
))

register_nodes('Vector', vector_math)
register_nodes('Scene', scene_nodes)
register_nodes('Bone', bone_nodes)
register_nodes('Math', math_nodes)
register_nodes('Variables', variable_nodes)
register_nodes('Default Nodes', default_nodes)

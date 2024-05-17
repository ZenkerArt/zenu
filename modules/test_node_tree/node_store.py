from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha1
from typing import Type, Iterable, Any

import nodeitems_utils
from bpy.types import NodeSocket
from .base_node import BaseNode


@dataclass
class ZenuNode:
    node: Type[BaseNode]
    cat: str

    @property
    def bl_id(self):
        name = self.node.__name__

        if hasattr(self.node, 'bl_idname'):
            name = self.node.bl_idname

        return name


class NodeStore:
    _nodes: list[ZenuNode]

    def __init__(self):
        self._nodes = []

    def add_node(self, cat_name: str, node: Type[BaseNode]):
        self._nodes.append(ZenuNode(
            node=node,
            cat=cat_name
        ))

    def add_nodes(self, cat_name: str, nodes: Iterable[Type[BaseNode]]):
        for i in nodes:
            self.add_node(cat_name, i)

    def get_classes(self):
        return tuple(i.node for i in self._nodes)

    def generate_nodes(self):
        nodes_cat = defaultdict(list)
        cats = []

        for i in self._nodes:
            nodes_cat[i.cat].append(nodeitems_utils.NodeItem(i.bl_id))

        for cat, nodes_cat in nodes_cat.items():
            cat = nodeitems_utils.NodeCategory(sha1(cat.encode()).hexdigest(), cat, items=nodes_cat)
            cats.append(cat)

        return cats


@dataclass
class ZenuSocket:
    socket: Type[NodeSocket]
    types: tuple[Any]
    register: bool = True

    @property
    def socket_name(self):
        if hasattr(self.socket, 'bl_idname'):
            return self.socket.bl_idname

        return self.socket.__name__


class SocketStore:
    _sockets: list[ZenuSocket]

    def __init__(self):
        self._sockets = []

    @property
    def sockets(self):
        return self._sockets
    def add_socket(self, socket: ZenuSocket):
        self._sockets.append(socket)

    def add_sockets(self, sockets: list[ZenuSocket]):
        for socket in sockets:
            self.add_socket(socket)

    def get_socket_name_by_type(self, typ: Any) -> ZenuSocket | None:
        for socket in self._sockets:
            has_type = typ in socket.types

            if has_type:
                return socket

    def get_classes(self):
        return tuple(socket.socket for socket in self._sockets if socket.register)


node_store = NodeStore()
socket_store = SocketStore()

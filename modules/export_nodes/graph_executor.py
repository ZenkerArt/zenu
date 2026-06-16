from collections import defaultdict, deque
from typing import Any, Iterable, Tuple
import bpy


class GraphExecutionDirection:
    FORWARD = 'FORWARD'
    BACKWARD = 'BACKWARD'


class GraphExecutor:
    def __init__(self, node_tree: bpy.types.NodeTree):
        self.tree = node_tree
        self.context: dict[bpy.types.Node, dict[str, Any]] = {}

    @staticmethod
    def collect_subgraph(start_node, sockets_exactly=None, direction=GraphExecutionDirection.BACKWARD):
        visited = set()
        stack = [start_node]

        while stack:
            node = stack.pop()
            if node in visited:
                continue

            visited.add(node)
            sockets = []
            node_dir = 'from_node' if direction == GraphExecutionDirection.BACKWARD else 'to_node'

            if sockets_exactly is not None:
                sockets = sockets_exactly
            elif direction == GraphExecutionDirection.BACKWARD:
                sockets = node.inputs
            elif direction == GraphExecutionDirection.FORWARD:
                sockets = node.outputs

            for socket in sockets:
                for link in socket.links:
                    stack.append(getattr(link, node_dir))

        return visited

    def build_links_for_subgraph(self, subgraph_nodes):
        return (
            (l.from_node, l.from_socket, l.to_node, l.to_socket)
            for l in self.tree.links
            if l.from_node in subgraph_nodes and l.to_node in subgraph_nodes
        )

    def build_graph(
            self,
            links: Iterable[
                Tuple[
                    bpy.types.Node,
                    bpy.types.NodeSocket,
                    bpy.types.Node,
                    bpy.types.NodeSocket,
                ]
            ],
    ):
        deps = defaultdict(set)  # to_node depends on from_node
        forward = defaultdict(set)  # from_node -> to_node

        for from_node, _, to_node, _ in links:
            deps[to_node].add(from_node)
            forward[from_node].add(to_node)

        return deps, forward

    def topo_sort(self, deps, forward):
        nodes = set(deps.keys()) | set(forward.keys())

        indegree = {n: len(deps[n]) for n in nodes}

        q = deque([n for n in nodes if indegree[n] == 0])
        order = []

        while q:
            n = q.popleft()
            order.append(n)

            for m in forward[n]:
                indegree[m] -= 1
                if indegree[m] == 0:
                    q.append(m)

        return order

    def get_link_data(self, link: bpy.types.NodeLink):
        from_socket = link.from_socket
        from_node = from_socket.node

        if from_node not in self.context:
            return None

        return self.context[from_node].get(from_socket.name)

    def eval_node(self, node):
        inputs = {}

        for socket in node.inputs:
            socket: bpy.types.NodeSocket

            if not socket.links:
                if hasattr(socket, "value"):
                    inputs[socket.name] = socket.value
                continue

            if socket.is_multi_input:
                value = [self.get_link_data(link) for link in socket.links]
            else:
                value = self.get_link_data(socket.links[0])

            if value is None:
                continue

            inputs[socket.name] = value

        if hasattr(node, "compute"):
            return node._pre_compute(**{**inputs, '_context': self.context})

        return {}

    def execute(self, node: bpy.types.Node, sockets_exactly = None, direction=GraphExecutionDirection.BACKWARD):
        sub_nodes = self.collect_subgraph(node, sockets_exactly=sockets_exactly, direction=direction)
        links = self.build_links_for_subgraph(sub_nodes)

        deps, forward = self.build_graph(links)

        order = self.topo_sort(deps, forward)

        for n in order:
            self.context[n] = self.eval_node(n)

        return self.context

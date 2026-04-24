from collections import defaultdict, deque
from typing import Any
import bpy


class GraphExecutor:
    def __init__(self, node_tree: bpy.types.NodeTree):
        self.tree = node_tree
        self.context: dict[bpy.types.Node, dict[str, Any]] = {}

    def collect_subgraph(self, target):
        visited = set()
        stack = [target]

        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)

            for inp in node.inputs:
                for link in inp.links:
                    stack.append(link.from_node)

        return visited

    def build_links_for_subgraph(self, subgraph_nodes):
        return (
            (l.from_node, l.from_socket, l.to_node, l.to_socket)
            for l in self.tree.links
            if l.from_node in subgraph_nodes and l.to_node in subgraph_nodes
        )

    def build_deps(self, links):
        deps = defaultdict(set)

        for from_node, _, to_node, _ in links:
            deps[to_node].add(from_node)

        return deps

    def topo_sort(self, deps):
        nodes = set(deps.keys())
        for v in deps.values():
            nodes |= v

        indegree = defaultdict(int)
        # for n in nodes:
        #     indegree[n] = 0

        for n in deps:
            for _ in deps[n]:
                indegree[n] += 1

        q = deque([n for n in nodes if indegree[n] == 0])
        order = []

        while q:
            n = q.popleft()
            order.append(n)
            for m in nodes:
                if n in deps[m]:
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
            if not socket.links:
                if hasattr(socket, 'value'):
                    inputs[socket.name] = socket.value
                continue

            value = self.get_link_data(socket.links[0])

            if len(socket.links) > 1:
                value = [self.get_link_data(link) for link in socket.links]

            if value is None:
                continue

            inputs[socket.name] = value

        if hasattr(node, "compute"):
            return node._pre_compute(**inputs)

        return {}

    def execute(self, node: bpy.types.Node):
        subgra = self.collect_subgraph(self.tree.nodes['Data Pack'])
        subgra = self.build_links_for_subgraph(subgra)

        deps = self.build_deps(subgra)
        order = self.topo_sort(deps)

        for node in order:
            self.context[node] = self.eval_node(node)

        return self.context

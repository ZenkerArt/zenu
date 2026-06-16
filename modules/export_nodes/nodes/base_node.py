import inspect
from typing import Any

import bpy


# from ..sockets import sockets


class BaseNode(bpy.types.Node):
    bl_idname = "BaseNode"
    bl_label = "Base Node"
    context: dict[Any, Any]

    def get_dependencies(self, ctx):
        return []

    def _pre_compute(self, **inputs):
        return self._post_compute(self.compute(**inputs))

    def _post_compute(self, result):
        return result

    def compute(self, **inputs):
        return inputs

    def get_input_link(self, name: str, link_index: int = 0) -> bpy.types.NodeLink | None:
        try:
            return self.inputs[name].links[link_index]
        except IndexError:
            return None
        except KeyError:
            return None

    def get_output_link(self, name: str, link_index: int = 0) -> bpy.types.NodeLink | None:
        try:
            return self.outputs[name].links[link_index]
        except IndexError:
            return None
        except KeyError:
            return None

    def restore_links(self, old_links_data):
        tree = self.id_data

        for link in list(tree.links):
            tree.links.remove(link)

        for data in old_links_data:
            from_node, from_socket_name, to_node, to_socket_name = data

            from_socket = from_node.outputs.get(from_socket_name)
            to_socket = to_node.inputs.get(to_socket_name)

            if from_socket and to_socket:
                tree.links.new(from_socket, to_socket)

    def recreate(self):
        out_value = {soc.name: soc.value for soc in self.outputs if hasattr(soc, 'value')}
        in_value = {soc.name: soc.value for soc in self.inputs if hasattr(soc, 'value')}

        # 1. save links
        old_links = [
            (l.from_node, l.from_socket.name,
             l.to_node, l.to_socket.name)
            for l in self.id_data.links
        ]

        # 2. rebuild sockets (DANGER)
        self.inputs.clear()
        self.outputs.clear()
        self.init(bpy.context)

        for name, value in out_value.items():
            try:
                self.outputs.get(name).value = value
            except AttributeError:
                pass

        for name, value in in_value.items():
            try:
                self.inputs.get(name).value = value
            except AttributeError:
                pass

        # 3. remove old links
        tree = self.id_data
        for l in list(tree.links):
            tree.links.remove(l)

        # 4. restore
        for from_node, from_sock, to_node, to_sock in old_links:
            fs = from_node.outputs.get(from_sock)
            ts = to_node.inputs.get(to_sock)

            if fs and ts:
                tree.links.new(fs, ts)


class SimpleNode(BaseNode):
    _output_convert: Any = None

    def init(self, context):
        sig = inspect.signature(self.compute)

        # type_map = {s.map_type: s for s in sockets}
        #
        # for name, param in sig.parameters.items():
        #     annotation = param.annotation
        #     self.inputs.new(type_map.get(annotation).bl_idname, name)
        #
        # for name, param in inspect.signature(sig.return_annotation).parameters.items():
        #     annotation = param.annotation
        #     socket = self.outputs.new(type_map.get(annotation).bl_idname, name)
        #     socket.hide_value = True

    def _pre_compute(self, **inputs):
        sig = inspect.signature(self.compute)

        for name, param in sig.parameters.items():
            if inputs.get(name) is None:
                inputs[name] = self.inputs.get(name).value

        return self._post_compute(self.compute(**inputs))

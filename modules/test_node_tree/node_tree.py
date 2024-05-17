import bpy


class TestNodeTree(bpy.types.NodeTree):
    bl_description = 'Zenu Test Node Tree'
    bl_label = "Test Node Tree"
    bl_icon = 'SEQUENCE_COLOR_04'
    bl_idname = "ZENU_test_node_tree"

    def update(self):
        bpy.app.timers.register(self.mark_invalid_links)

    def mark_invalid_links(self):
        for link in self.links:
            if link.to_node.bl_idname == 'ZENU_ND_execute_node': continue
            if not isinstance(link.from_socket, type(link.to_socket)):
                link.is_valid = False

    @classmethod
    def valid_socket_type(cls, idname: str) -> bool:
        print(idname)
        return False

import subprocess

import bpy
from nodeitems_utils import NodeCategory

from . import sockets, nodes, node_categories
from .graph_executor import GraphExecutor
from .utils import get_registers
from ...base_panel import BasePanel


class ZENU_OT_reload_node_system(bpy.types.Operator):
    bl_label = 'Reload Node System'
    bl_idname = 'zenu.reload_node_system'

    def execute(self, context: bpy.types.Context):
        filepath = bpy.data.filepath

        if not filepath:
            self.report({'WARNING'}, "File not saved")
            return {'CANCELLED'}

        bpy.ops.wm.save_mainfile()

        blender_exe = bpy.app.binary_path

        subprocess.Popen([blender_exe, filepath])

        bpy.ops.wm.quit_blender()

        return {'FINISHED'}


class ZENU_OT_execute_node_system(bpy.types.Operator):
    bl_label = 'Execute Node System'
    bl_idname = 'zenu.execute_node_system'

    def execute(self, context: bpy.types.Context):
        graph = GraphExecutor(bpy.data.node_groups['Reload Node Tree'])
        graph.execute(bpy.data.node_groups['Reload Node Tree'].users['Data Pack'])

        # graph.execute()
        return {'FINISHED'}


class ZENU_OT_recreate_node_system(bpy.types.Operator):
    bl_label = 'Recreate Node System'
    bl_idname = 'zenu.recreate_node_system'

    def execute(self, context: bpy.types.Context):
        for i in bpy.data.node_groups['Reload Node Tree'].users:
            i.recreate()
        return {'FINISHED'}


class ExportNodeTree(bpy.types.NodeTree):
    bl_idname = "ExportNodeTree"
    bl_label = "Export Node Editor"
    bl_icon = 'NODETREE'

    def update(self):
        if not hasattr(self, "nodes"):
            return

        for node in self.nodes:
            for socket in node.inputs:
                for link in socket.links:
                    try:
                        val = socket.poll(node, link)
                        if not val:
                            self.links.remove(link)
                    except Exception:
                        pass


class MyNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "ExportNodeTree"


class ZENU_PT_export_nodes(BasePanel):
    bl_label = 'Export Nodes'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_reload_node_system.bl_idname)
        layout.operator(ZENU_OT_execute_node_system.bl_idname)
        layout.operator(ZENU_OT_recreate_node_system.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ExportNodeTree,
    ZENU_OT_reload_node_system,
    ZENU_OT_execute_node_system,
    ZENU_OT_recreate_node_system,
    ZENU_PT_export_nodes,
))

nodes_file = get_registers(nodes)


def register():
    reg()
    nodes_file.register()
    sockets.register()
    node_categories.register()


def unregister():  # dd
    unreg()
    nodes_file.unregister()

    sockets.unregister()
    node_categories.unregister()
    # nodeitems_utils.unregister_node_categories("MY_NODES")

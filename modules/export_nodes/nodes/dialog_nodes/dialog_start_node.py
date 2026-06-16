import json
from typing import Any

import bpy

from . import BaseDialogNode
from .dialog_line_node import DialogLineNode
from ... import node_categories, GraphExecutor
from ...dependency import DependencyCollection, DependencyExporter
from ...graph_executor import GraphExecutionDirection
from ...sockets.armature_socket import ArmatureTypeSocket
from ...sockets.dialog_socket import DialogSocketType, DialogContext
from ....base_operator.action_operator import ActionOperator


class DialogNodeComplier:
    _context: DialogContext
    _armatures: list[ArmatureTypeSocket.Response]
    _deps: DependencyCollection

    def __init__(self, node: BaseDialogNode, context: DialogContext, node_context: Any):
        self._context = context
        self._node_context = node_context
        self._armatures = node_context[node].get('armatures')

        self._deps = DependencyCollection()

        for node in self._context.nodes:
            node: BaseDialogNode
            self._deps.add_dep(node.get_dependencies(self._context))

    def collect_deps(self):
        return self._deps

    def config_build(self, export_deps: DependencyExporter):
        links = {}
        nodes = {}
        entry = ''

        for from_node, to_node in self._context.forward_links.items():
            links[from_node.name] = {'to': tuple(i.name for i in to_node), 'to_node': tuple(i for i in to_node)}

        for node in self._context.nodes:
            if node.dialog_type == 'start':
                entry = links[node.name]['to'][0]
                continue

            dct = {
                'type': node.dialog_type,
                'to': []
            }
            data = links.get(node.name)

            if data is not None:
                dct['to'] = data['to']

            nodes[node.name] = dct

            if node.dialog_type == 'choice':
                dct['options'] = [{'to': i.name, 'text': i.dialog_text} for i in data['to_node']]

            if node.dialog_type == 'line':
                deps = self._deps.get_by_node(node)
                idle = None
                enter = None

                if not deps:
                    continue

                for dep in deps:
                    if dep.meta.get('type') == 'idle':
                        idle = dep
                    if dep.meta.get('type') == 'enter':
                        enter = dep
                dct['text'] = node.dialog_text
                dct['animation_enter'] = None
                dct['animation_idle'] = None

                if enter is not None:
                    dct['animation_enter'] = export_deps.get_name(enter)

                if idle is not None:
                    dct['animation_idle'] = export_deps.get_name(idle)

        return {
            'dialogEntry': entry,
            'dialog': nodes,
        }


class DialogStartNodeActions(ActionOperator):
    bl_label = 'Dialog Start Node Actions'
    mute: bpy.props.BoolProperty(default=True)

    node_system: bpy.props.StringProperty()
    node: bpy.props.StringProperty()

    def action_execute(self, context: bpy.types.Context):
        ns = bpy.data.node_groups[self.node_system]
        node: DialogStartNode = ns.nodes[self.node]

        node_context = GraphExecutor(ns).execute(node, direction=GraphExecutionDirection.FORWARD)
        dialog_context: DialogContext = node_context[node].get('dialog')
        armatures: list[ArmatureTypeSocket.Response] = node_context[node].get('armatures')
        dialog_context.context['meta'] = {
            'armatures': armatures
        }

        comp = DialogNodeComplier(node, dialog_context, node_context)
        deps = comp.collect_deps()

        dep_export = DependencyExporter(r'D:\Addons\zenu_scenes\ExportNodes\Test2\\', deps)

        data = json.dumps({
            **comp.config_build(dep_export),
            'deps': dep_export.export()
        }, indent=2)

        print(data)

        dep_export.save_config(data)
        DialogContext.print_tree(dialog_context, node)


class DialogStartNode(BaseDialogNode):
    bl_idname = "DialogStartNode"
    bl_label = "Dialog Start"
    dialog_type = 'start'

    def draw_buttons(self, context, layout):
        row = layout.row()
        op = DialogStartNodeActions.draw_action(row, DialogStartNodeActions.action_execute)
        op.node_system = self.id_data.name
        op.node = self.name

    def init(self, context):
        self.outputs.new(DialogSocketType.bl_idname, 'dialog')
        self.inputs.new(ArmatureTypeSocket.bl_idname, 'armatures', use_multi_input=True)

    def compute(self, **inputs):
        dialog_context = DialogContext()
        dialog_context.add_link(self, self.get_output_link('dialog').to_node)
        armatures = []

        for link in self.inputs['armatures'].links:
            armatures.append(link.from_node.compute()['armature'])

        return {
            'dialog': dialog_context,
            'armatures': armatures
        }


reg, unreg = bpy.utils.register_classes_factory((
    DialogStartNode,
    DialogStartNodeActions.gen_op(),
))


def register():
    node_categories.dialog.add_node(DialogStartNode)
    reg()


def unregister():
    unreg()

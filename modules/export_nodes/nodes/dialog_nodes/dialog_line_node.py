import bpy

from . import BaseDialogNode
from ... import node_categories
from ...dependency import Dependency, DepType
from ...sockets.armature_socket import ArmatureSocketResponse
from ...sockets.dialog_socket import DialogSocketType, DialogContext
from ...utils import activate_animation


class ZENU_OT_open_dialog_animation(bpy.types.Operator):
    bl_label = 'Open Dialog Animation'
    bl_idname = 'zenu.open_dialog_animation'

    node_system: bpy.props.StringProperty()
    node: bpy.props.StringProperty()
    action: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        node = bpy.data.node_groups[self.node_system].nodes[self.node]

        start_node = node.get_start_node()
        armatures: list[ArmatureSocketResponse] = start_node.compute()['armatures']

        activate_animation(bpy.data.actions[self.action], armatures)

        self.report({'INFO'}, f'Open action {self.action}')
        return {'FINISHED'}


class DialogLineNode(BaseDialogNode):
    bl_idname = "DialogLineNode"
    bl_label = "Dialog Line"
    dialog_type = 'line'

    dialog_text: bpy.props.StringProperty()
    order: bpy.props.IntProperty(soft_min=0, soft_max=10, subtype='FACTOR')
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    action_idle: bpy.props.PointerProperty(type=bpy.types.Action)
    sound: bpy.props.StringProperty()

    def get_start_node(self, start_node: BaseDialogNode = None):
        if start_node is None:
            start_node = self

        try:
            node = start_node.inputs['dialog'].links[0].from_node
        except KeyError:
            return None

        if node.dialog_type == 'start':
            return node

        return self.get_start_node(node)

    def draw_buttons(self, context, layout):


        col = layout.column_flow(align=True)

        link = self.get_input_link('dialog')

        col.prop(self, 'dialog_text', text='', placeholder='Dialog Text')
        if link is not None and hasattr(link.from_node, 'has_order'):
            col.prop(self, 'order', text='', placeholder='Order')

        box = layout.box().column_flow(align=True)
        box.label(text='Enter Animation')
        box.prop(self, 'action', text='')
        box.prop_search(self, 'sound', context.scene.sequence_editor, 'strips', text='')

        if self.action is not None:
            op = box.operator(ZENU_OT_open_dialog_animation.bl_idname, text='Edit Enter')
            op.node_system = self.id_data.name
            op.node = self.name
            op.action = self.action.name

        box = layout.box().column_flow(align=True)
        box.label(text='Idle Animation')
        box.prop(self, 'action_idle', text='')
        if self.action_idle is not None:
            op = box.operator(ZENU_OT_open_dialog_animation.bl_idname, text='Edit Idle')
            op.node_system = self.id_data.name
            op.node = self.name
            op.action = self.action_idle.name

    def init(self, context):
        self.outputs.new(DialogSocketType.bl_idname, 'dialog')
        self.inputs.new(DialogSocketType.bl_idname, 'dialog')

    def get_dependencies(self, ctx: DialogContext):
        deps = []

        sound = bpy.context.scene.sequence_editor.strips.get(self.sound)
        if self.action is not None:
            deps.append(Dependency(
                dep_type=DepType.ANIMATION,
                resource=self.action,
                node=self,
                meta={
                    'type': 'enter',
                    'armatures': ctx.context['meta'].get('armatures')
                }
            ))

        if self.action_idle is not None:
            deps.append(Dependency(
                dep_type=DepType.ANIMATION,
                resource=self.action_idle,
                node=self,
                meta={
                    'type': 'idle',
                    'armatures': ctx.context['meta'].get('armatures')
                }
            ))

        if sound is not None:
            deps.append(Dependency(
                dep_type=DepType.SOUND,
                resource=sound,
                node=self
            ))
        return deps

    def compute(self, **inputs):
        dialog_context: DialogContext = inputs.get('dialog')
        if dialog_context is None:
            return {}

        link = self.get_output_link('dialog')

        if link is None:
            return {}
        dialog_context.add_link(self, link.to_node)
        return inputs


reg, unreg = bpy.utils.register_classes_factory((
    DialogLineNode,
    ZENU_OT_open_dialog_animation
))


def register():
    node_categories.dialog.add_node(DialogLineNode)
    reg()


def unregister():
    unreg()

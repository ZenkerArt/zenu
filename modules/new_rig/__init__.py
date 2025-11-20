from .action_list import rig_action_list
from ..base_operator.action_operator import ActionOperator
from .layers import BoneCollectionLayer, BoneCollectorLayer, CopyLayer, RigComponentsLayer, CopyConstraintLayer, StyleLayer, ActionsLayer
from .rig_lib import DepsInject, RigLayers, RigContext
from .builtin_components import components
from ...base_panel import BasePanel
import bpy


class RigActions(ActionOperator):
    bl_label = 'Rig Action'

    @staticmethod
    def switch_arm(obj1, obj2):
        bpy.ops.object.mode_set(mode='OBJECT')
        obj1.hide_set(True)
        bpy.ops.object.select_all(action='DESELECT')

        obj2.select_set(True)
        obj2.hide_set(False)
        bpy.context.view_layer.objects.active = obj2

        bpy.ops.object.mode_set(mode='POSE')

    def action_back(self, context: bpy.types.Context):
        rig_settings = context.active_object.zenu_rig_props
        rig_type: str = rig_settings.rig_type
        link_rig: bpy.types.Object = rig_settings.link_rig

        if rig_type == 'META' or rig_type == 'GENERATED':
            self.switch_arm(context.active_object, link_rig)


class ZENU_OT_generate_rig(bpy.types.Operator):
    bl_label = 'Generate Rig'
    bl_idname = 'zenu.generate_rig'
    bl_options = {'UNDO'}

    def create_armature(self, name: str):
        armature = bpy.data.armatures.get(name)
        if armature is None:
            armature = bpy.data.armatures.new(name)

        new_armature = bpy.data.objects.get(name)

        if new_armature is None:
            new_armature = bpy.data.objects.new(name, armature)

        try:
            bpy.context.scene.collection.objects.link(new_armature)
        except RuntimeError:
            pass

        return new_armature

    def get_armatures(self, context: bpy.types.Context):
        arm = context.active_object

        new_arm = None
        org_arm = None

        if arm.zenu_rig_props.rig_type == 'GENERATED':
            new_arm = arm
            org_arm = arm.zenu_rig_props.link_rig
        elif arm.zenu_rig_props.rig_type == 'META':
            new_arm = arm.zenu_rig_props.link_rig
            org_arm = arm

        if new_arm is None:
            new_arm = self.create_armature(f'RIG-{org_arm.name}')

        return new_arm, org_arm

    def execute(self, context: bpy.types.Context):
        new_arm, org_arm = self.get_armatures(context)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        org_arm.select_set(True)
        org_arm.hide_set(False)
        context.view_layer.objects.active = org_arm

        new_arm.zenu_rig_props.link_rig = org_arm
        new_arm.zenu_rig_props.rig_type = 'GENERATED'
        org_arm.zenu_rig_props.link_rig = new_arm

        new_arm.hide_set(False)

        RigActions.switch_arm(org_arm, new_arm)

        inject = DepsInject([
            RigContext(),
            CopyLayer(),
            BoneCollectorLayer(),
            BoneCollectionLayer(),
            RigComponentsLayer(components),
            CopyConstraintLayer(),
            ActionsLayer(),
            StyleLayer()
        ])

        rig_context = inject.get_by_type(RigContext)
        rig_context.original_armature = org_arm
        rig_context.new_armature = new_arm
        rig_context.deps = inject

        rig_layers = RigLayers(rig_context)
        rig_layers.add_layer(inject.get_by_type(CopyLayer))
        rig_layers.add_layer(inject.get_by_type(BoneCollectorLayer))
        rig_layers.add_layer(inject.get_by_type(BoneCollectionLayer))
        rig_layers.add_layer(inject.get_by_type(RigComponentsLayer))
        rig_layers.add_layer(inject.get_by_type(CopyConstraintLayer))
        rig_layers.add_layer(inject.get_by_type(ActionsLayer))
        rig_layers.add_layer(inject.get_by_type(StyleLayer))
        rig_layers.execute()
        org_arm.hide_set(True)
        return {'FINISHED'}


class ZENU_PT_new_rig(BasePanel):
    bl_label = 'New Rig'
    bl_context = ''

    def draw_mesh_settings(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object

        if not isinstance(obj.data, bpy.types.Mesh):
            return

        settings: ZenuRigShape = obj.zenu_rig_shape
        layout.prop(settings, 'is_shape')
        layout.prop(settings, 'name')

    def draw_actions(self, layout: bpy.types.UILayout):
        obj = bpy.context.active_object

        rig_action_list.draw_ui(layout)

        if rig_action_list.active is None:
            return
        col = layout.column(align=True)
        col.scale_y = 1.3
        col.prop(rig_action_list.active, 'mirror',
                 icon='MOD_MIRROR', text='Mirror')
        col.prop_search(rig_action_list.active, 'bone',
                        obj.data, 'bones', text='')
        
        if rig_action_list.active.mirror:
                col.prop_search(rig_action_list.active, 'mirror_bone',
                    obj.data, 'bones', text='')
        
        col.prop(rig_action_list.active, 'action', text='')

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        if context.active_object is None:
            return

        self.draw_mesh_settings(context, layout)

        if not isinstance(context.active_object.data, bpy.types.Armature):
            return

        row = layout.row(align=True)
        row.operator(ZENU_OT_generate_rig.bl_idname)
        RigActions.draw_action(row, RigActions.action_back, 'Back')

        obj = context.active_object
        col = layout.column(align=True)
        col.prop(obj.zenu_rig_props, 'rig_type',
                 text='', icon='APPEND_BLEND')

        if context.active_pose_bone is None:
            return

        bone = context.active_pose_bone.bone

        col = layout.column()
        props = bone.zenu_rig_component_props

        col.prop(props, 'component_id', text='')
        col.prop(props, 'shape', text='')

        if obj.zenu_rig_props.rig_type == 'META':
            for i in components:
                if str(i.get_n_id()) != props.component_id:
                    continue
                i.draw(context, props, col)
                break

            header, panel = layout.panel('action_draw', default_closed=False)
            header.label(text='Actions')
            if panel:
                self.draw_actions(panel)


def components_items(self, scene):
    d = [
        ('-1', 'None', '')
    ]

    for i in components:
        d.append((
            str(i.get_n_id()), i.name, ''
        ))
    return d


def shapes(self, scene):
    d = [
        ('none', 'None', '')
    ]

    for i in bpy.data.objects:
        if not i.zenu_rig_shape.is_shape:
            continue

        d.append((
            i.name, i.zenu_rig_shape.name, ''
        ))

    return d


def shape_filter(self, object: bpy.types.Object):
    if object.type != 'MESH':
        return False

    return object.zenu_rig_shape.is_shape


dct = {}

for i in components:
    dct = {
        **dct,
        **i.get_props_for_register()
    }

data = {
    '__annotations__': {
        'component_id': bpy.props.EnumProperty(items=components_items),
        'shape': bpy.props.PointerProperty(type=bpy.types.Object, poll=shape_filter),
        **dct
    }
}


RigProps = type("RigProps", (bpy.types.PropertyGroup,), data)


class ZenuRig(bpy.types.PropertyGroup):
    rig_type: bpy.props.EnumProperty(items=(
        ('NONE', 'None', ''),
        ('META', 'Meta Rig', ''),
        ('GENERATED', 'Generated Rig', '')
    ), name='Rig Type')
    link_rig: bpy.props.PointerProperty(type=bpy.types.Object)


class ZenuRigShape(bpy.types.PropertyGroup):
    is_shape: bpy.props.BoolProperty(default=False)
    name: bpy.props.StringProperty()


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_new_rig,
    ZENU_OT_generate_rig,
    RigActions.gen_op(),
    ZenuRigShape,
    RigProps,
    ZenuRig
))


def register():
    reg()
    rig_action_list.register()
    bpy.types.Object.zenu_rig_shape = bpy.props.PointerProperty(
        type=ZenuRigShape)

    bpy.types.Object.zenu_rig_props = bpy.props.PointerProperty(
        type=ZenuRig)
    bpy.types.Bone.zenu_rig_component_props = bpy.props.PointerProperty(
        type=RigProps)


def unregister():
    unreg()
    rig_action_list.unregister()

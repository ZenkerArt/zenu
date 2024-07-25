import os

import bpy
from rna_prop_ui import rna_idprop_quote_path
from ...utils import is_type, get_path_to_asset, get_collection
from .meta_bone import MetaBoneData
from ...base_panel import BasePanel
from .rigs import rig_modules

rig_types = tuple((i.id, i.rig_name, '', i.n_id) for i in rig_modules)


def select_armature(context: bpy.types.Context, obj: bpy.types.Object):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    context.view_layer.objects.active = obj
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='POSE')


class MetaBoneType:
    NONE = 'NONE'


class MetaBoneMode:
    ADD = 'ADD'
    NEW = 'NEW'


class MetaBone(bpy.types.PropertyGroup):
    type: bpy.props.EnumProperty(items=(
        (MetaBoneType.NONE, 'None', ''),
        *rig_types
    ))


def target_poll(self: 'MetaBoneSettings', obj: bpy.types.Object):
    if self.id_data == obj.data:
        return False

    return is_type(obj, bpy.types.Armature)


class MetaBoneSettings(bpy.types.PropertyGroup):
    mode: bpy.props.EnumProperty(items=(
        (MetaBoneMode.ADD, 'Add', 'Add bones to current armature'),
        (MetaBoneMode.NEW, 'New', 'Add bones to target armature'),
    ))
    target: bpy.props.PointerProperty(type=bpy.types.Object, poll=target_poll)
    is_can_generated: bpy.props.BoolProperty(default=True)


class MetaBoneDep(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)


class ZENU_OT_back_to_rig(bpy.types.Operator):
    bl_label = 'Back To Meta Rig'
    bl_idname = 'zenu.back_to_rig'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        try:
            return not context.active_object.data.zenu_meta_settings.is_can_generated
        except AttributeError:
            return False

    def execute(self, context: bpy.types.Context):
        select_armature(context, context.active_object.data.zenu_meta_settings.target)
        return {'FINISHED'}


class ZENU_OT_generate_rig(bpy.types.Operator):
    bl_label = 'Generate Rig'
    bl_idname = 'zenu.generate_rig'
    bl_options = {'UNDO'}

    def apply_to_bones(self, context: bpy.types.Context, bones):
        for bone in bones:
            meta = MetaBoneData.from_pose_bone(bone)

            for module in rig_modules:
                if meta.meta.type != module.id: continue

                module.bone = meta

                bpy.ops.object.mode_set(mode='EDIT')
                module.execute_edit(context)
                name = meta.name
                arm = meta.obj

                bpy.ops.object.mode_set(mode='POSE')
                module.bone = MetaBoneData.from_pose_bone(arm.pose.bones[name])
                module.execute_pose(context)

                module.styles.apply_styles(meta.obj)
                break

    def prepare_new_armature(self, context: bpy.types.Context):
        bpy.ops.object.mode_set(mode='POSE')
        original_obj = context.active_object
        new_obj: bpy.types.Object = context.active_object.data.zenu_meta_settings.target

        for i in new_obj.data.zenu_meta_deps:
            try:
                bpy.data.objects.remove(i.obj, do_unlink=True)
            except Exception:
                pass

        new_obj.data.zenu_meta_deps.clear()

        name = original_obj.data.name
        new_data = original_obj.data.copy()
        new_data.zenu_meta_settings.is_can_generated = False
        new_data.zenu_meta_settings.target = original_obj

        for module in rig_modules:
            module.regenerate(context, original_obj, new_obj)

        old_data = new_obj.data
        old_data.name = f'{name}_Remove'

        new_obj.data = new_data
        bpy.data.armatures.remove(old_data, do_unlink=True)

        new_obj.data.name = f'{name}_Generated'
        new_obj.name = original_obj.name + '_Edit'

        drivers_data = new_obj.animation_data.drivers

        for dr in drivers_data:
            new_obj.driver_remove(dr.data_path, -1)

        select_armature(context, new_obj)
        return new_obj

    def execute(self, context: bpy.types.Context):
        obj = None

        if context.active_object.data.zenu_meta_settings.mode == MetaBoneMode.NEW:
            obj = self.prepare_new_armature(context)

            for bone in obj.pose.bones:
                for c in bone.constraints:
                    bone.constraints.remove(c)

        if obj is None:
            obj = context.active_object

        self.apply_to_bones(context, obj.pose.bones)
        return {'FINISHED'}


class ZENU_OT_generate_shape_enum(bpy.types.Operator):
    bl_label = 'Generate Shape Enum'
    bl_idname = 'zenu.generate_shape_enum'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        path = get_path_to_asset('ZenuRigAssets.blend')

        with bpy.data.libraries.load(path) as (data_from, data_to):
            text = 'class ShapesEnum:'

            for i in data_from.objects:
                name = i.split("-")[1]
                text += f"\n    {name} = '{i}'"
            print(text)

        return {'FINISHED'}


class ZENU_PT_rig(BasePanel):
    bl_label = 'Rig'
    bl_context = ''

    def generate_settings(self, context: bpy.types.Context):
        bone = context.active_bone
        obj = context.active_object
        arm = obj.data

        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 1.4
        row = col.row(align=True)
        r = row.row()
        r.scale_x = .6
        r.prop(arm.zenu_meta_settings, 'mode', text='')
        row.operator(ZENU_OT_generate_rig.bl_idname)

        if arm.zenu_meta_settings.mode == MetaBoneMode.NEW:
            col.prop(arm.zenu_meta_settings, 'target', text='')

        if bone is None or context.active_pose_bone is None:
            return

        layout.prop(bone.zenu_meta_bone, 'type', text='')

        bone = MetaBoneData.from_bone(context.active_pose_bone, obj)

        for i in rig_modules:
            if i.id == bone.meta.type:
                i.layout = self.layout.box()
                i.bone = bone
                i.draw(context)

    def draw(self, context: bpy.types.Context):
        # self.layout.operator(ZENU_OT_generate_shape_enum.bl_idname)

        obj = context.active_object

        if obj is None:
            return

        arm = obj.data

        if is_type(arm, bpy.types.Armature) and arm.zenu_meta_settings.is_can_generated:
            self.generate_settings(context)
        else:
            self.layout.operator(ZENU_OT_back_to_rig.bl_idname)

        keys = obj.keys()

        if not len(keys):
            return

        box = self.layout.box()
        for prop_name in keys:
            if not prop_name.startswith('zenu_'): continue
            new_name = prop_name.replace('zenu_', '')
            new_name = new_name.split('_')
            new_name = ' '.join(new_name).title()

            box.prop(obj, rna_idprop_quote_path(prop_name), text=new_name)


dct = {}

for i in rig_modules:
    dct = {
        **dct,
        **i.get_blender_props()
    }

data = {
    '__annotations__': dct
}

RigProps = type("RigProps", (bpy.types.PropertyGroup,), data)

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_rig,
    ZENU_OT_generate_rig,
    ZENU_OT_back_to_rig,
    ZENU_OT_generate_shape_enum,
    MetaBone,
    RigProps,
    MetaBoneSettings,
    MetaBoneDep
))


def register():
    reg()
    bpy.types.Bone.zenu_meta_bone = bpy.props.PointerProperty(type=MetaBone)
    bpy.types.Bone.zenu_meta_props = bpy.props.PointerProperty(type=RigProps)
    bpy.types.Armature.zenu_meta_settings = bpy.props.PointerProperty(type=MetaBoneSettings)
    bpy.types.Armature.zenu_meta_deps = bpy.props.CollectionProperty(type=MetaBoneDep)

    for module in rig_modules:
        module._register()


def unregister():
    unreg()

    for module in rig_modules:
        module._unregister()

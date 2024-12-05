import bpy
from bpy.props import BoolProperty
from .config import SPACE_SWITCH_POSTFIX, SWITCHER_OBJECT, TARGET_OBJECT, IS_SWITCHER, COPY_ROTATION, COPY_LOCATION, \
    ACTION_PREFIX
from .utils import remove_constraint, switch_armature, remove_switcher, get_target_and_switcher, remove_bone, \
    get_switch_object, get_armature_name, setup_armature, get_bones_info, create_bones, add_constraints
from ...base_panel import BasePanel


def setup_space_switch_armature(target_obj: bpy.types.Object, bones: list[bpy.types.PoseBone]):
    scene = bpy.context.scene
    obj = setup_armature(target_obj)
    bones_info = get_bones_info(obj, bones)
    create_bones(obj, bones_info)
    add_constraints(obj, target_obj, bones_info)

    bpy.ops.nla.bake(
        frame_start=scene.frame_start,
        frame_end=scene.frame_end,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=True,
        use_current_action=True,
        channel_types={'LOCATION', 'ROTATION', 'SCALE'},
        bake_types={'POSE'})
    obj.animation_data.action.name = f'{ACTION_PREFIX}{target_obj.animation_data.action.name}'
    add_constraints(target_obj, obj, bones_info, has_space_switch=True)


class ZENU_OT_sp_create_armature(bpy.types.Operator):
    bl_label = 'Create Bones'
    bl_idname = 'zenu.sp_create_armature'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        selected_bones = bpy.context.selected_pose_bones
        target_obj = bpy.context.active_object

        if not selected_bones:
            self.report({'WARNING'}, "Please select a bone to apply the space switch")
            return {'CANCELLED'}

        if target_obj.get(IS_SWITCHER):
            target_obj = get_switch_object(target_obj)
            switch_armature(target_obj, mode='POSE')

        remove_bone(target_obj, selected_bones)

        setup_space_switch_armature(target_obj, selected_bones)

        return {'FINISHED'}


class ZENU_OT_sp_clear_bone(bpy.types.Operator):
    bl_label = 'Create Empty'
    bl_idname = 'zenu.sp_armature_clear'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        remove_switcher(context.active_object)
        return {'FINISHED'}


class ZENU_OT_sp_bake_all(bpy.types.Operator):
    bl_label = 'Switch'
    bl_idname = 'zenu.sp_bake_all'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        target, switcher = get_target_and_switcher(obj)
        scene = context.scene
        switch_armature(target, mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        for sp_bone in switcher.data.bones:
            bone = target.pose.bones[sp_bone.name]
            bone.bone.select = True

        bpy.ops.nla.bake(
            frame_start=scene.frame_start,
            frame_end=scene.frame_end,
            step=1,
            only_selected=True,
            visual_keying=True,
            clear_constraints=False,
            use_current_action=True,
            channel_types={'LOCATION', 'ROTATION', 'SCALE'},
            bake_types={'POSE'})

        for sp_bone in switcher.data.bones:
            bone = target.pose.bones[sp_bone.name]
            remove_constraint(bone)

        remove_switcher(obj)

        return {'FINISHED'}


class ZENU_OT_sp_switch(bpy.types.Operator):
    bl_label = 'Switch'
    bl_idname = 'zenu.sp_switch'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        name = obj.get(TARGET_OBJECT, None) or obj.get(SWITCHER_OBJECT, None)
        if name is not None:
            target_obj = bpy.data.objects[name]
            switch_armature(target_obj, mode='POSE')

        return {'FINISHED'}


class ZENU_OT_sp_remove_select(bpy.types.Operator):
    bl_label = 'Remove Bone'
    bl_idname = 'zenu.sp_remove_select'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        obj = context.active_object

        remove_bone(obj, context.selected_pose_bones)

        return {'FINISHED'}


class ZENU_PT_space_switcher(BasePanel):
    bl_label = 'Space Switcher'
    bl_context = ''
    enable_constraints = BoolProperty(name="Enable Constraints", default=True)

    def draw(self, context):
        layout = self.layout

        obj = get_switch_object(context.active_object)

        col = layout.column(align=True)
        row = col.row(align=True)

        row.operator(ZENU_OT_sp_create_armature.bl_idname, text='Bake', icon='PINNED')
        row.scale_y = 1.5
        row.alert = True

        if obj:
            row.operator(ZENU_OT_sp_clear_bone.bl_idname, text='', icon='TRASH', )
            col.operator(ZENU_OT_sp_switch.bl_idname, text='Switch Armature', icon='ARROW_LEFTRIGHT')
            layout.operator(ZENU_OT_sp_remove_select.bl_idname, text='Remove Select', icon='REMOVE')
            layout.operator(ZENU_OT_sp_bake_all.bl_idname, text='Bake To Original')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_sp_create_armature,
    ZENU_OT_sp_clear_bone,
    ZENU_OT_sp_switch,
    ZENU_OT_sp_bake_all,
    ZENU_OT_sp_remove_select,
    ZENU_PT_space_switcher
))


def register():
    reg()


def unregister():
    unreg()

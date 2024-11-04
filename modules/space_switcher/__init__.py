from dataclasses import dataclass

import bpy
from bpy.props import BoolProperty
from mathutils import Matrix, Vector
from ..rig.shapes import get_shape, ShapesEnum
from ...base_panel import BasePanel
from ...utils import get_collection

COPY_LOCATION = 'COPY_LOCATION_SPACE_SWITCHING'
COPY_ROTATION = 'COPY_ROTATION_SPACE_SWITCHING'
SPACE_SWITCH_POSTFIX = '_Space_Switch_Armature'
TARGET_OBJECT = 'sp_target_object'
SWITCHER_OBJECT = 'sp_switcher_object'
IS_SWITCHER = 'sp_is_switcher'


def switch_armature(obj: bpy.types.Object, mode='EDIT'):

    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode='OBJECT')

    obj.select_set(True)
    bpy.ops.object.mode_set(mode=mode)


def get_target_and_switcher(obj: bpy.types.Object):
    value = obj.get(TARGET_OBJECT, False)

    if value:
        return bpy.data.objects[value], obj

    value = obj.get(SWITCHER_OBJECT, False)

    if value:
        return obj, bpy.data.objects[value]

    return None


def remove_switcher(obj: bpy.types.Object):
    target, switcher = get_target_and_switcher(obj)

    coll = get_collection(f'ZenuSpaceSwitching_Armatures')

    for bone in switcher.data.bones:
        pose_bone = target.pose.bones[bone.name]
        for constraint in pose_bone.constraints:
            if hasattr(constraint, 'target'):
                if constraint.target == switcher:
                    pose_bone.constraints.remove(constraint)

    bpy.data.armatures.remove(switcher.data)

    if len(coll.objects) <= 0:
        bpy.data.collections.remove(coll)


    switch_armature(target, mode='POSE')


@dataclass
class SPBoneInfo:
    head: Vector
    tail: Vector
    len: float
    armature_name: str
    name: str


def get_armature_name(name: str):
    return f'{name}{SPACE_SWITCH_POSTFIX}'


class ZENU_OT_sp_create_armature(bpy.types.Operator):
    bl_label = 'Create Bones'
    bl_idname = 'zenu.sp_create_armature'
    bl_options = {'UNDO'}

    @staticmethod
    def create_or_get_armature(name: str) -> tuple[bpy.types.Object, bpy.types.Armature]:
        obj = bpy.data.objects.get(name)

        if obj is not None:
            return obj, obj.data

        arm: bpy.types.Armature = bpy.data.armatures.get(name)

        if arm is not None:
            bpy.data.armatures.remove(arm)

        arm = bpy.data.armatures.new(name)
        obj = bpy.data.objects.new(name, arm)
        return obj, arm

    def execute(self, context: bpy.types.Context):
        selected_bones = bpy.context.selected_pose_bones
        target_obj = bpy.context.active_object
        coll = get_collection(f'ZenuSpaceSwitching_Armatures')
        armature_name = get_armature_name(context.active_object.name)
        scene = context.scene

        obj, arm = self.create_or_get_armature(armature_name)

        obj[TARGET_OBJECT] = target_obj.name
        target_obj[SWITCHER_OBJECT] = obj.name

        target_obj[IS_SWITCHER] = False
        obj[IS_SWITCHER] = True

        if coll.objects.find(obj.name) == -1:
            coll.objects.link(obj)

        if not selected_bones:
            self.report({'WARNING'}, "Please select a bone to apply the space switch")
            return {'CANCELLED'}

        bones_info = []

        for bone in selected_bones:
            if arm.bones.get(bone.name) is not None:
                continue

            bones_info.append(SPBoneInfo(
                name=bone.name,
                armature_name=target_obj.name,
                tail=bone.tail @ target_obj.matrix_basis,
                head=bone.head @ target_obj.matrix_basis,
                len=bone.length
            ))

        switch_armature(obj, mode='EDIT')

        for bone_info in bones_info:
            bone = arm.edit_bones.get(bone_info.name)

            if bone is not None:
                bones_info.remove(bone_info)
                continue

            bone = arm.edit_bones.new(bone_info.name)
            bone.length = bone_info.len / 3

        bpy.ops.object.mode_set(mode='POSE')

        for bone_info in bones_info:
            bone = obj.pose.bones[bone_info.name]
            bone.custom_shape = get_shape(ShapesEnum.SphereDirWire)
            bone.bone.select = True

            constraint: bpy.types.CopyRotationConstraint = bone.constraints.new('COPY_ROTATION')

            constraint.target = target_obj
            constraint.subtarget = bone_info.name

            constraint: bpy.types.CopyRotationConstraint = bone.constraints.new('COPY_LOCATION')

            constraint.target = target_obj
            constraint.subtarget = bone_info.name

        bpy.ops.nla.bake(
            frame_start=scene.frame_start,
            frame_end=scene.frame_end,
            step=1,
            only_selected=True,
            visual_keying=True,
            clear_constraints=True,
            use_current_action=True,
            bake_types={'POSE'})

        switch_armature(target_obj, mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        for bone_info in bones_info:
            bone = target_obj.pose.bones[bone_info.name]
            bone.bone.select = True

            constraint: bpy.types.CopyRotationConstraint = bone.constraints.new('COPY_ROTATION')
            constraint.name = COPY_ROTATION

            constraint.target = obj
            constraint.subtarget = bone_info.name

            constraint: bpy.types.CopyRotationConstraint = bone.constraints.new('COPY_LOCATION')
            constraint.name = COPY_LOCATION

            constraint.target = obj
            constraint.subtarget = bone_info.name

            bone['has_space_switch'] = True

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
            bake_types={'POSE'})

        for sp_bone in switcher.data.bones:
            bone = target.pose.bones[sp_bone.name]

            for constraint in bone.constraints:
                if constraint.name in (COPY_LOCATION, COPY_ROTATION):
                    bone.constraints.remove(constraint)

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


class ZENU_PT_space_switcher(BasePanel):
    bl_label = 'Space Switcher'
    bl_context = ''
    enable_constraints = BoolProperty(name="Enable Constraints", default=True)

    def draw(self, context):
        layout = self.layout

        layout.operator(ZENU_OT_sp_create_armature.bl_idname, text='Space Switch Bone')
        layout.operator(ZENU_OT_sp_clear_bone.bl_idname, text='Space Switch Clear Bone')
        layout.operator(ZENU_OT_sp_bake_all.bl_idname, text='Space Switch Bake All')
        layout.operator(ZENU_OT_sp_switch.bl_idname, text='Switch')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_sp_create_armature,
    ZENU_OT_sp_clear_bone,
    ZENU_OT_sp_switch,
    ZENU_OT_sp_bake_all,
    ZENU_PT_space_switcher
))


def register():
    reg()


def unregister():
    unreg()

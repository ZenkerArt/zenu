from dataclasses import dataclass

import bpy
from mathutils import Vector
from .config import TARGET_OBJECT, SWITCHER_OBJECT, COPY_ROTATION, COPY_LOCATION, SPACE_SWITCH_POSTFIX, IS_SWITCHER
from ..rig.shapes import get_shape
from ...utils import get_collection


@dataclass
class SPBoneInfo:
    head: Vector
    tail: Vector
    len: float
    armature_name: str
    name: str


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


def get_target_and_switcher(obj: bpy.types.Object) -> tuple[bpy.types.Object, bpy.types.Object]:
    value = obj.get(TARGET_OBJECT, False)

    if value:
        return bpy.data.objects[value], obj

    value = obj.get(SWITCHER_OBJECT, False)

    if value:
        return obj, bpy.data.objects[value]

    return None


def remove_bone(obj: bpy.types.Object, bones: list[bpy.types.PoseBone]):
    try:
        target, switcher = get_target_and_switcher(obj)
    except Exception:
        return
    switcher_arm: bpy.types.Armature = switcher.data
    action = switcher.animation_data.action

    names = [i.name for i in bones]
    for name in names:
        pose_bone = target.pose.bones[name]
        switch_armature(switcher, mode='EDIT')

        for i in list(action.fcurves):
            if i.group.name == name:
                # i.id_data.remove(i)
                action.fcurves.remove(i)

        for constraint in pose_bone.constraints:
            if hasattr(constraint, 'target'):
                if constraint.target == switcher:
                    pose_bone.constraints.remove(constraint)

        try:
            switcher_arm.edit_bones.remove(switcher_arm.edit_bones[name])
        except KeyError:
            pass
    switch_armature(target, mode='POSE')


def remove_switcher(obj: bpy.types.Object):
    target, switcher = get_target_and_switcher(obj)

    coll = get_collection(f'ZenuSpaceSwitching_Armatures')

    for bone in switcher.data.bones:
        pose_bone = target.pose.bones[bone.name]
        for constraint in pose_bone.constraints:
            if hasattr(constraint, 'target'):
                if constraint.target == switcher:
                    pose_bone.constraints.remove(constraint)

    bpy.data.actions.remove(switcher.animation_data.action)
    bpy.data.armatures.remove(switcher.data)

    if len(coll.objects) <= 0:
        bpy.data.collections.remove(coll)

    switch_armature(target, mode='POSE')


def remove_constraint(bone: bpy.types.PoseBone):
    for constraint in bone.constraints:
        if constraint.name in (COPY_LOCATION, COPY_ROTATION):
            bone.constraints.remove(constraint)


def get_armature_name(name: str):
    return f'{name}{SPACE_SWITCH_POSTFIX}'


def get_switch_object(obj: bpy.types.Object) -> bpy.types.Object | None:
    name = obj.get(TARGET_OBJECT, None) or obj.get(SWITCHER_OBJECT, None)

    if name is None:
        return None

    return bpy.data.objects.get(name, None)


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


def get_bones_info(obj: bpy.types.Object, bones: list[bpy.types.PoseBone]) -> list[SPBoneInfo]:
    arm: bpy.types.Armature = obj.data
    bones_info = []

    for bone in bones:
        if arm.bones.get(bone.name) is not None:
            continue
        remove_constraint(bone)

        bones_info.append(SPBoneInfo(
            name=bone.name,
            armature_name=obj.name,
            tail=bone.tail @ obj.matrix_basis,
            head=bone.head @ obj.matrix_basis,
            len=bone.length
        ))

    return bones_info


def add_constraints(obj: bpy.types.Object, target_obj: bpy.types.Object, bones: list[SPBoneInfo],
                    has_space_switch: bool = False):
    switch_armature(obj, mode='POSE')
    for bone in bones:
        bone = obj.pose.bones[bone.name]

        if not has_space_switch:
            bone.custom_shape = get_shape('WGT-SphereWire')

        bone.bone.select = True

        constraint: bpy.types.CopyRotationConstraint = bone.constraints.new('COPY_ROTATION')

        constraint.target = target_obj
        constraint.subtarget = bone.name

        constraint: bpy.types.CopyRotationConstraint = bone.constraints.new('COPY_LOCATION')

        constraint.target = target_obj
        constraint.subtarget = bone.name

        if has_space_switch:
            bone['has_space_switch'] = True


def create_bones(obj: bpy.types.Object, bones: list[bpy.types.PoseBone]):
    arm: bpy.types.Armature = obj.data

    switch_armature(obj, mode='EDIT')
    for bone_info in bones:
        bone = arm.edit_bones.get(bone_info.name)

        if bone is not None:
            bones.remove(bone_info)
            continue

        bone = arm.edit_bones.new(bone_info.name)
        bone.length = bone_info.len / 3
    return bones


def setup_armature(target_obj: bpy.types.Object) -> bpy.types.Object:
    coll = get_collection(f'ZenuSpaceSwitching_Armatures')
    armature_name = get_armature_name(target_obj.name)
    obj, arm = create_or_get_armature(armature_name)

    obj[TARGET_OBJECT] = target_obj.name
    target_obj[SWITCHER_OBJECT] = obj.name

    target_obj[IS_SWITCHER] = False
    obj[IS_SWITCHER] = True

    if coll.objects.find(obj.name) == -1:
        coll.objects.link(obj)

    return obj

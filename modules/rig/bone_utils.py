import re

import bpy.types
from mathutils import Vector


def pos_to_char(pos):
    if pos > 25:
        return pos

    return chr(pos + 97).title()


def bone_name_format(bone: bpy.types.EditBone, name: str = None, prefix: str = None, postfix: str = None):
    if name is None:
        name = bone.name

    if postfix is not None:
        name += postfix

    if prefix is not None:
        name = prefix + name

    return name


def _create_bone(bone: bpy.types.EditBone, name: str = None, prefix: str = None, postfix: str = None) -> bpy.types.EditBone:
    name = bone_name_format(bone, name, prefix, postfix)
    return bone.id_data.edit_bones.new(name)


def bone_copy_transforms(src: bpy.types.EditBone, dst: bpy.types.EditBone):
    dst.length = src.length
    dst.matrix = src.matrix.copy()


def bone_disable_deform(bones: list[bpy.types.EditBone]):
    for bone in bones:
        bone.use_deform = False


def bone_clone(bone: bpy.types.EditBone, name: str = None, prefix: str = None,
               postfix: str = None) -> bpy.types.EditBone:
    """Work only in edit mode, not copy constraints, creates new bone with same transformations"""
    new_bone = _create_bone(bone, name, prefix, postfix)
    new_bone.color.palette = bone.color.palette
    bone_copy_transforms(bone, new_bone)

    return new_bone


def bone_create_lerp(bone: bpy.types.EditBone, factor: float, name: str = None, prefix: str = None,
                     postfix: str = None):
    new_bone = bone_clone(bone, name, prefix, postfix)
    new_bone.length = new_bone.length + 1

    new_bone.head = bone.head.lerp(bone.tail, factor)
    new_bone.length = bone.length
    return new_bone


def bone_connect(bones: list[bpy.types.EditBone], use_connect: bool = True, revers: bool = False):
    prev_bone = None

    if revers:
        bones = reversed(bones)

    for bone in bones:
        bone.use_connect = use_connect
        bone.parent = prev_bone
        prev_bone = bone

    return bones


def bone_subdivide(bone: bpy.types.EditBone, subdivide: int, name: str = None) -> list[bpy.types.EditBone]:
    bones = []

    if not name:
        name = bone.name

    length = bone.length / subdivide
    bone = bone_create_lerp(bone, 0)
    bone.length = length
    bone.name = f'{name}_A'

    bones.append(bone)

    for i in range(0, subdivide - 1):
        bone = bone_create_lerp(bone, 1)
        bone.name = f'{name}_{pos_to_char(i + 1)}'
        bones.append(bone)

    return bones


def bone_get_side(bone: any) -> str:
    name: str = bone.name
    name = name.lower()

    n = re.findall(r'.*(left$|right$|[._\- ][lr]$)', name)

    if n:
        return n[0].upper()

    return ''


def bone_get_head(bone: bpy.types.PoseBone) -> Vector:
    arm: bpy.types.Object = bone.id_data
    mat = arm.matrix_world @ bone.matrix

    return mat.translation


def bone_get_tail(bone: bpy.types.PoseBone) -> Vector:
    return bone_get_head(bone) + bone.vector

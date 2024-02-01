import bpy
from ...utils import is_type, check_mods


def only_armature(obj: bpy.types.Object) -> bool:
    return is_type(obj, bpy.types.Armature)


def only_armature_weight(obj: bpy.types.Object) -> bool:
    if len(bpy.context.selected_objects) <= 1:
        return False

    return is_type(obj, bpy.types.Armature) and check_mods('o')


def only_mesh(obj: bpy.types.Object) -> bool:
    return is_type(obj, bpy.types.Mesh)


def only_edit_mesh(obj: bpy.types.Object) -> bool:
    return is_type(obj, bpy.types.Mesh) and check_mods('e')


def any_object(obj: bpy.types.Object) -> bool:
    return True

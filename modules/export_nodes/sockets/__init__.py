import bpy

from . import (
    test_socket,
    object_socket,
    string_socket,
    mask_socket,
    character_equipment_socket,
    any_socket,
    file_socket,
    dialog_socket,
    armature_socket,
    dialog_animation_socket,
    dialog_modifier
)

mods = [
    test_socket,
    object_socket,
    string_socket,
    mask_socket,
    character_equipment_socket,
    any_socket,
    file_socket,
    dialog_socket,
    armature_socket,
    dialog_animation_socket,
    dialog_modifier
]


def register():
    for mod in mods:
        mod.register()


def unregister():
    for mod in mods:
        mod.unregister()

import os

import bpy.types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ZenUtilsPreferences

COLOR_ICONS = ('SEQUENCE_COLOR_01', 'SEQUENCE_COLOR_02', 'SEQUENCE_COLOR_03', 'SEQUENCE_COLOR_04', 'SEQUENCE_COLOR_05',
               'SEQUENCE_COLOR_06', 'SEQUENCE_COLOR_07', 'SEQUENCE_COLOR_08', 'SEQUENCE_COLOR_09')


def get_path_to_asset(filename: str):
    return os.path.join(os.path.dirname(__file__), 'assets/', filename)


def register_modules(modules):
    for i in modules:
        i.register()


def unregister_modules(modules):
    for i in modules:
        try:
            i.unregister()
        except Exception as e:
            print(e)


def exit_from_nla(obj: bpy.types.Object):
    area = None

    for i in bpy.context.screen.areas:
        if i.ui_type == 'NLA_EDITOR':
            area = i

    if area is None:
        raise RuntimeError('NLA Area not found.')

    try:
        with bpy.context.temp_override(area=area, active_object=obj, object=obj):
            bpy.ops.nla.tweakmode_exit()
        return True
    except RuntimeError:
        return False


def nla_pushdown(obj: bpy.types.Object):
    area = None

    for i in bpy.context.screen.areas:
        if i.ui_type == 'NLA_EDITOR':
            area = i

    if area is None:
        raise RuntimeError('NLA Area not found.')

    with bpy.context.temp_override(area=area, active_object=obj, object=obj):
        bpy.ops.nla.tracks_add()
        bpy.ops.nla.action_pushdown()


def nla_duplicate(obj: bpy.types.Object):
    area = None

    for i in bpy.context.screen.areas:
        if i.ui_type == 'NLA_EDITOR':
            area = i

    if area is None:
        raise RuntimeError('NLA Area not found.')

    with bpy.context.temp_override(area=area, active_object=obj, object=obj):
        bpy.ops.nla.duplicate()


def update_window(all_w: bool = False):
    try:
        for region in bpy.context.area.regions:
            if all_w:
                region.tag_redraw()
                continue
            if region.type == 'WINDOW':
                region.tag_redraw()
    except AttributeError:
        pass


def get_prefs() -> 'ZenUtilsPreferences':
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    return addon_prefs


def get_modifier(obj: bpy.types.Object, mod: bpy.types.Modifier | str):
    try:
        return get_all_modifiers(obj, mod)[0]
    except IndexError:
        return None


def get_all_modifiers(obj: bpy.types.Object, mod: bpy.types.Modifier | str):
    if obj is None:
        return None

    if isinstance(mod, str):
        cloth = [i for i in obj.modifiers if i.type == mod]
    else:
        cloth = [i for i in obj.modifiers if isinstance(i, mod)]

    return cloth


def get_collection(name: str, color: str = 'COLOR_04'):
    collection = bpy.data.collections.get(name)

    if collection:
        return collection

    collection = bpy.data.collections.new(name)
    collection.color_tag = color
    bpy.context.scene.collection.children.link(collection)
    return collection


def check_mods(mods: str):
    mods = mods.lower()
    if bpy.context.object is None:
        return False
    args = []
    for i in mods:
        args.append(getattr(Mods, i))
    return any(bpy.context.object.mode == mod for mod in args)


def is_mesh(obj: bpy.types.Object):
    return obj and obj.data and isinstance(obj.data, bpy.types.Mesh)


def is_type(obj: bpy.types.Object, type: bpy.types.AnyType):
    if not isinstance(obj, bpy.types.Object):
        return isinstance(obj, type)

    return obj and obj.data and isinstance(obj.data, type)


class Mods:
    p: str = 'POSE'
    w: str = 'WEIGHT_PAINT'
    o: str = 'OBJECT'
    e: str = 'EDIT'
    t: str = 'TEXTURE_PAINT'
    v: str = 'VERTEX_PAINT'
    s: str = 'SCULPT'

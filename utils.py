import bpy.types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ZenUtilsPreferences


def update_window():
    for region in bpy.context.area.regions:
        if region.type == 'WINDOW':
            region.tag_redraw()


def get_prefs() -> 'ZenUtilsPreferences':
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    return addon_prefs


def get_modifier(obj: bpy.types.Object, mod: bpy.types.Modifier | str):
    if obj is None:
        return None

    if isinstance(mod, str):
        cloth = [i for i in obj.modifiers if i.type == mod]
    else:
        cloth = [i for i in obj.modifiers if isinstance(i, mod)]

    try:
        return cloth[0]
    except IndexError:
        return None


def get_collection(name: str, color: str = 'COLOR_04'):
    collection = bpy.data.collections.get(name)

    if collection:
        return collection

    for coll in bpy.data.collections:
        if not coll.is_lod:
            continue
        return coll

    collection = bpy.data.collections.new(name)
    collection.color_tag = color
    collection.is_lod = True
    bpy.context.scene.collection.children.link(collection)
    return collection


def check_mods(mods: str):
    if bpy.context.object is None:
        return False
    args = []
    for i in mods:
        args.append(getattr(Mods, i))
    return any(bpy.context.object.mode == mod for mod in args)


class Mods:
    p: str = 'POSE'
    w: str = 'WEIGHT_PAINT'
    o: str = 'OBJECT'
    e: str = 'EDIT'
    t: str = 'TEXTURE_PAINT'
    v: str = 'VERTEX_PAINT'
    s: str = 'SCULPT'

import bpy
from bpy.types import ClothModifier


def get_cloth(obj: bpy.types.Object) -> ClothModifier | None:
    if not isinstance(obj, bpy.types.Object):
        return None

    cloth = [i for i in obj.modifiers if isinstance(i, ClothModifier)]
    try:
        return cloth[0]
    except IndexError:
        return None



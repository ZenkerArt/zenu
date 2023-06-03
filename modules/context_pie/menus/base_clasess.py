from abc import ABC

import bpy
from ..context_group import Drawer
from ....utils import is_type


class ObjectDrawer(Drawer, ABC):
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object and not is_type(context.active_object, bpy.types.Armature)


class ArmatureDrawer(Drawer, ABC):
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_type(context.active_object, bpy.types.Armature)

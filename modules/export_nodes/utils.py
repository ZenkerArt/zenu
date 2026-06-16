import importlib
import pkgutil
from typing import Any, TYPE_CHECKING
import bpy

if TYPE_CHECKING:
    from .dependency import Dependency
    from .sockets.armature_socket import ArmatureSocketResponse


class ObjectTypes:
    MESH = 'MESH'
    ARMATURE = 'ARMATURE'
    NONE = 'NONE'


def object_filter(self, value):
    if self.filter_type == ObjectTypes.NONE:
        return True

    return value.type == self.filter_type


def object_filter_static(filter_type: str):
    def object_filter_temp(self, value):
        if filter_type == ObjectTypes.NONE:
            return True

        return value.type == filter_type

    return object_filter_temp


class ModuleReg:
    _mods: list[Any]

    def __init__(self, mods):
        self._mods = mods

    def register(self):
        for i in self._mods:
            i.register()

    def unregister(self):
        for i in self._mods:
            i.unregister()


def get_registers(package: Any):
    nodes = []

    for m in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(m.name)

            if hasattr(module, "register") and callable(module.register):
                nodes.append(module)
        except ImportError as error:
            print(error)

    return ModuleReg(nodes)


def get_slot(action: bpy.types.Action, slot_name: str):
    for sl in action.slots:
        if sl.name_display == slot_name:
            return sl

    return None


def activate_animation(action: bpy.types.Action, armatures: list['ArmatureSocketResponse']):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.use_preview_range = False
    if action.use_frame_range:
        bpy.context.scene.use_preview_range = True

        bpy.context.scene.frame_preview_start = int(action.frame_start)
        bpy.context.scene.frame_preview_end = int(action.frame_end)


    for arm in armatures:
        obj = arm.armature

        obj.select_set(True)
        obj.animation_data.action_blend_type = 'REPLACE'
        obj.animation_data.action = action
        obj.animation_data.action_slot = get_slot(action, arm.action_slot_name)

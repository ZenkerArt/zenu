from dataclasses import dataclass
from hashlib import sha1
from typing import Any, Self, Type, TypeVar
import bpy
from .rig_bone import RigBone

T = TypeVar('T')


@dataclass
class BoneConvertResult:
    results: list[RigBone]

    @property
    def first_result(self):
        try:
            return self.results[0]
        except IndexError:
            pass


def fullname(o, is_instance: bool = True) -> str:
    if is_instance:
        klass = o.__class__
    else:
        klass = o
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__
    return module + '.' + klass.__qualname__


class RigComponent:
    name = 'Rig Base'
    armature_obj: bpy.types.Object

    def __init__(self):
        self.id = sha1((self.name + fullname(self)).encode()).hexdigest()
        self.n_id = int(self.id, 16) % (10 ** 4)

    @classmethod
    def get_id(cls):
        return sha1((cls.name + fullname(cls, is_instance=False)).encode()).hexdigest()

    @classmethod
    def get_n_id(cls):
        return int(cls.get_id(), 16) % (10 ** 4)

    @classmethod
    def get_prop_name(cls, item: str):
        n_id = cls.get_n_id()

        return f'{cls.__name__}_{n_id}_{item}'

    @classmethod
    def get_props_for_register(cls) -> dict[str, bpy.types.Property]:
        properties = {}
        for key, value in cls.__annotations__.items():
            key = cls.get_prop_name(key)
            if type(value).__name__ == '_PropertyDeferred':
                properties[key] = value
        return properties

    @classmethod
    def get_prop_value(cls, bone, item):
        if isinstance(bone, bpy.types.PoseBone):
            bone = bone.bone
        if isinstance(bone, bpy.types.EditBone):
            bone = bone.id_data.bones[bone.name]

        return getattr(bone.zenu_rig_component_props, cls.get_prop_name(item))

    def get_edit_bones_by_names(self, names: list[str]) -> tuple[bpy.types.EditBone]:
        return tuple(self.armature_obj.data.edit_bones[name] for name in names)

    def get_pose_bones_by_names(self, names: list[str]) -> tuple[bpy.types.PoseBone]:
        return tuple(self.armature_obj.pose.bones[name] for name in names)

    def convert_bone(self, bone: Any) -> BoneConvertResult:
        if isinstance(bone, list):
            return BoneConvertResult(results=[self.convert_bone(i).first_result for i in bone])
        elif hasattr(bone, 'name'):
            return BoneConvertResult(results=[RigBone(self.armature_obj, bone.name)])
        return BoneConvertResult(results=[])

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        pass

    def execute_object(self):
        pass

    def execute_edit(self):
        pass

    def execute_pose(self):
        pass

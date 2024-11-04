import uuid
from abc import ABC
from dataclasses import dataclass, field
from typing import Callable, Any
from hashlib import sha1
import bpy.types
from typing import TYPE_CHECKING

from mathutils import Vector
from ..shapes import get_shape

if TYPE_CHECKING:
    from ..meta_bone import MetaBoneData


def fullname(o) -> str:
    klass = o.__class__
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__
    return module + '.' + klass.__qualname__


@dataclass
class RigStyleItem:
    bone_name: str
    shape: str
    color: str

    scale: Vector = field(default_factory=lambda: Vector((1, 1, 1)))
    translate: Vector = field(default_factory=lambda: Vector((0, 0, 0)))
    rotation: Vector = field(default_factory=lambda: Vector((0, 0, 0)))


class RigStyleContainer:
    _styles: list[RigStyleItem]

    def __init__(self):
        self._styles = []

    def add(self, bone_name: str, shape: str, color: str = 'THEME03'):
        item = RigStyleItem(
            bone_name=bone_name,
            shape=shape,
            color=color
        )

        self._styles.append(item)

        return item

    def apply_styles(self, obj: bpy.types.Object):
        for i in self._styles:
            try:
                bone = obj.pose.bones[i.bone_name]
                bone.color.palette = i.color
                bone.custom_shape = get_shape(i.shape)

                bone.custom_shape_scale_xyz = i.scale
                bone.custom_shape_rotation_euler = i.rotation
                bone.custom_shape_translation = i.translate
            except Exception as e:
                print(e)


class RigBoneCollection:
    _obj: bpy.types.Object
    _armature: bpy.types.Armature

    def __init__(self, obj: bpy.types.Object):
        self._obj = obj
        self._armature = obj.data

    def get_collection(self, name: str):
        arm = self._armature
        collection = arm.collections.get(name)

        if collection is None:
            collection = arm.collections.new(name)

        return collection

    def add_bone(self, name: str, bone: Any):
        if hasattr(bone, 'collections'):
            for i in bone.collections:
                i.unassign(bone)

        collection = self.get_collection(name)
        collection.assign(bone)


class RigBoneDefaultCollection:
    _bone_collection: RigBoneCollection

    def __init__(self, bone_collection: RigBoneCollection):
        self._bone_collection = bone_collection

    def add_deform(self, bone: Any):
        self._bone_collection.add_bone('DEF', bone)

    def add_mch(self, bone: Any):
        self._bone_collection.add_bone('MCH', bone)

    def add_tweakers(self, bone: Any):
        self._bone_collection.add_bone('Tweakers', bone)

    def add_fk(self, bone: Any):
        self._bone_collection.add_bone('FK', bone)

    def add_ik(self, bone: Any):
        self._bone_collection.add_bone('IK', bone)


class RigModule(ABC):
    _reg: Callable = None
    _unreg: Callable = None
    rig_name: str = 'No Name'
    id: str = ''
    n_id: int = 0
    layout: bpy.types.UILayout
    styles: RigStyleContainer
    bone: 'MetaBoneData'
    collection: RigBoneCollection
    coll: RigBoneDefaultCollection

    def __init__(self):
        self.id = sha1(fullname(self).encode()).hexdigest()
        self.n_id = int(self.id, 16) % (10 ** 4)
        self.styles = RigStyleContainer()
        self.init()

    def _pre_init(self):
        pass

    @staticmethod
    def pre_init(mod: 'RigModule'):
        mod._pre_init()
        mod.collection = RigBoneCollection(mod.bone.obj)
        mod.coll = RigBoneDefaultCollection(mod.collection)

    def init(self):
        pass

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError as e:
            return getattr(self.bone.props, self.get_prop_name(item))

    @classmethod
    def get_prop_name(cls, item: str):
        return f'{cls.__name__}_{item}'

    @classmethod
    def get_blender_props(cls) -> dict[str, bpy.types.Property]:
        properties = {}
        for key, value in cls.__annotations__.items():
            key = cls.get_prop_name(key)
            if type(value).__name__ == '_PropertyDeferred':
                properties[key] = value
        return properties

    @property
    def props(self):
        return self.bone.props

    def register(self) -> tuple:
        return tuple()

    def unregister(self):
        pass

    def _register(self):
        self._reg, self._unreg = bpy.utils.register_classes_factory(self.register())
        self._reg()

    def _unregister(self):
        if self._unreg is None:
            return
        self.unregister()
        self._unreg()
        self._unreg = None

    def add_dep(self, obj: bpy.types.Object):
        dep = self.bone.arm.zenu_meta_deps.add()
        dep.obj = obj

    def draw(self, context: bpy.types.Context):
        pass

    def regenerate(self, context: bpy.types.Context, original_arm: bpy.types.Object, new_arm: bpy.types.Object):
        pass

    def execute_pose(self, context: bpy.types.Context):
        pass

    def execute_edit(self, context: bpy.types.Context):
        pass

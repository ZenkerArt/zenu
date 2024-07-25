import uuid
from abc import ABC
from dataclasses import dataclass, field
from typing import Callable
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


class RigModule(ABC):
    _reg: Callable = None
    _unreg: Callable = None
    rig_name: str = 'No Name'
    id: str = ''
    n_id: int = 0
    layout: bpy.types.UILayout
    styles: RigStyleContainer
    bone: 'MetaBoneData'

    def __init__(self):
        self.id = sha1(fullname(self).encode()).hexdigest()
        self.n_id = int(self.id, 16) % (10 ** 4)
        self.styles = RigStyleContainer()
        self.init()

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

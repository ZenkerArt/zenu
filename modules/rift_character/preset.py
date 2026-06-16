from dataclasses import dataclass, field, asdict

import bpy.types


@dataclass
class ShapeProperty:
    shape: str
    function: str

    @classmethod
    def to_json(cls, value: dict):
        return cls(**value)


@dataclass
class Preset:
    name: str
    category: str
    properties: list[ShapeProperty] = field(default_factory=list)

    def to_dict(self):
        return {
            'name': self.name,
            'category': self.category,
            'properties': [asdict(prop) for prop in self.properties]
        }

    @classmethod
    def from_dict(cls, dct: dict):
        properties = dct.pop('properties')

        self = cls(**dct)

        for prop in properties:
            self.properties.append(ShapeProperty.to_json(prop))
        return self

    def get_object_shapes(self, objs: list[bpy.types.Object]) -> list[tuple[bpy.types.ShapeKey, ShapeProperty]]:
        shape_keys = []

        for obj in objs:
            for prop in self.properties:
                shape_key = obj.data.shape_keys.key_blocks.get(prop.shape)

                if shape_key is None: continue

                shape_keys.append((
                    shape_key,
                    prop
                ))

        return shape_keys


class Presets:
    _presets: list[Preset]
    _presets_name: dict[str, Preset]
    _cat_split: dict[str, list[Preset]]

    def __init__(self, presets: list[Preset]):
        self._presets = presets

        self._presets_name = {preset.name: preset for preset in presets}

        self._cat_split = {}

        for preset in presets:
            cat = self._cat_split.get(preset.category.lower()) or []
            cat.append(preset)
            self._cat_split[preset.category.lower()] = cat

    def all(self):
        return self._presets

    def get_by_name(self, name: str):
        return self._presets_name.get(name)

    def get_dynamic_enum(self, category: str):
        def func(s, context):
            return [(i.name, i.name, '') for i in self._cat_split[category]]
        return func

    def get_by_enum_index(self, category: str, index: int):
        return self._cat_split[category][index]




def load_presets(lst: list):
    return Presets([Preset.from_dict(i) for i in lst])

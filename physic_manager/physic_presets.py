import json
import os
from dataclasses import dataclass
from typing import Any

import bpy

path = os.path.join(os.path.dirname(__file__), '../assets/physic_presets')




@dataclass
class PhysicPreset:
    name: str

    @property
    def preset_path(self):
        return os.path.join(path, f'{self.name}.json')

    def __post_init__(self):
        if os.path.exists(self.preset_path):
            return

        with open(self.preset_path, 'w') as f:
            f.write('{}')

    def load(self) -> dict[str, Any]:
        with open(self.preset_path, 'r') as f:
            return json.loads(f.read())

    def save(self, dct: dict):
        with open(self.preset_path, 'w') as f:
            f.write(json.dumps(dct, indent=2))

    def remove(self):
        if os.path.exists(self.preset_path):
            os.remove(self.preset_path)


def get_current_preset() -> PhysicPreset | None:
    try:
        data = [i for i in physic_presets if i.name.upper() == bpy.context.scene.physic_presets][0]
    except IndexError:
        return

    return data

physic_presets: list[PhysicPreset] = []

for i in os.scandir(path):
    physic_presets.append(PhysicPreset(name=i.name.rsplit('.')[0]))

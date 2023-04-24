import typing
from dataclasses import dataclass

import bpy


@dataclass
class Keybinding:
    bind: bpy.types.KeyMapItem


class Keybindings:
    _key_map: bpy.types.KeyMap
    _keys: list[Keybinding]

    def __init__(self, name: str, space: str):
        self._keys = []

        key_config = bpy.context.window_manager.keyconfigs.addon
        self._key_map = key_config.keymaps.new(name=name, space_type=space)

    def new(self,
                 idname: str,
                 type: typing.Union[int, str],
                 value: typing.Union[int, str],
                 any: bool = False,
                 shift: int = 0,
                 ctrl: int = 0,
                 alt: int = 0,
                 oskey: int = 0,
                 key_modifier: typing.Union[int, str] = 'NONE',
                 direction: typing.Union[int, str] = 'ANY',
                 repeat: bool = False,
                 head: bool = False
                 ):
        pass

    # def remove(self, ):


keybindings: list[Keybinding] = []


def add_binding(key_entry: bpy.types.KeyMapItem):
    keybindings.append(Keybinding(bind=key_entry))

import typing
from dataclasses import dataclass
from inspect import currentframe, getframeinfo

import bpy


@dataclass
class Keybinding:
    bind: bpy.types.KeyMapItem


class Keybindings:
    _key_map: bpy.types.KeyMap
    _keys: list[Keybinding]
    _name: str
    _space: str

    def __init__(self, name: str, space_type: str):
        self._keys = []
        self._name = name
        self._space = space_type

    def new(self,
            idname: str,
            type: typing.Union[int, str],
            value: typing.Union[int, str] = 'PRESS',
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
        key_entry = self._key_map.keymap_items.new(
            idname=idname,
            type=type,
            value=value,
            any=any,
            shift=shift,
            ctrl=ctrl,
            alt=alt,
            oskey=oskey,
            key_modifier=key_modifier,
            direction=direction,
            repeat=repeat,
            head=head
        )
        self._keys.append(Keybinding(bind=key_entry))
        
    def remove(self, type: str):
        for i in self._keys:
            if i.bind.type == type:
                self._keys.remove(i)

    def register(self):
        try:
            key_config = bpy.context.window_manager.keyconfigs.addon
            self._key_map = key_config.keymaps.new(name=self._name, space_type=self._space)
        except Exception:
            pass

    def unregister(self):
        try:
            for i in self._keys:
                self._key_map.keymap_items.remove(i.bind)
        except Exception:
            pass


dopesheet = Keybindings(name='Dopesheet', space_type='DOPESHEET_EDITOR')
graph_editor = Keybindings(name='Graph Editor', space_type='GRAPH_EDITOR')
view_3d = Keybindings(name='3D View', space_type='VIEW_3D')

key_spaces = (
    view_3d,
    dopesheet,
    graph_editor
)

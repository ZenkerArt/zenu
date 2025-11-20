import typing
from dataclasses import dataclass
from inspect import currentframe, getframeinfo

import bpy


@dataclass
class Keybinding:
    idname: str
    type: typing.Union[int, str]
    value: typing.Union[int, str] = 'PRESS'
    any: bool = False
    shift: int = 0
    ctrl: int = 0
    alt: int = 0
    oskey: int = 0
    key_modifier: typing.Union[int, str] = 'NONE'
    direction: typing.Union[int, str] = 'ANY'
    repeat: bool = False
    head: bool = False
    bind: bpy.types.KeyMapItem = None


class Keybindings:
    _key_map: bpy.types.KeyMap = None
    _keys: list[Keybinding]
    _keys_wait_to_register: list[Keybinding]
    _name: str
    _space: str

    def __init__(self, name: str, space_type: str):
        self._keys = []
        self._keys_wait_to_register = []
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

        keybind = Keybinding(
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
            head=head)
        
        self._register_bind(keybind)

    def remove(self, type: str):
        for i in self._keys:
            if i.bind.type == type:
                self._keys.remove(i)

    def _register_bind(self, keybinding: Keybinding):
        if self._key_map is None:
            self._keys_wait_to_register.append(keybinding)
            return

        key_entry = self._key_map.keymap_items.new(
            idname=keybinding.idname,
            type=keybinding.type,
            value=keybinding.value,
            any=keybinding.any,
            shift=keybinding.shift,
            ctrl=keybinding.ctrl,
            alt=keybinding.alt,
            oskey=keybinding.oskey,
            key_modifier=keybinding.key_modifier,
            direction=keybinding.direction,
            repeat=keybinding.repeat,
            head=keybinding.head
        )

        keybinding.bind = key_entry

        self._keys.append(keybinding)

    def register(self):
        print(self._space)
        key_config = bpy.context.window_manager.keyconfigs.addon
        self._key_map = key_config.keymaps.new(name=self._name, space_type=self._space)
        

        for i in self._keys_wait_to_register:
            self._register_bind(i)

        self._keys_wait_to_register.clear()
    def unregister(self):
        try:
            for i in self._keys:
                self._key_map.keymap_items.remove(i.bind)
        except Exception:
            pass


dopesheet = Keybindings(name='Dopesheet', space_type='DOPESHEET_EDITOR')
sequence_editor = Keybindings(name='Sequence Editor', space_type='SEQUENCE_EDITOR')
graph_editor = Keybindings(name='Graph Editor', space_type='GRAPH_EDITOR')
view_3d = Keybindings(name='3D View', space_type='VIEW_3D')

key_spaces = (
    view_3d,
    dopesheet,
    graph_editor,
    sequence_editor,
)

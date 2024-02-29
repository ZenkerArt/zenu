from dataclasses import dataclass

import blf
import bpy
from mathutils import Vector


@dataclass
class DrawerShortcut:
    key: str
    desc: str = ''
    is_active: bool = False


class Drawer:
    _draw_id: int = None
    _shortcuts: list[DrawerShortcut]
    _font_size: int = 16
    _padding_x: int = 20
    _padding_y: int = 20

    def __init__(self):
        self._shortcuts = []

    def add_shortcut(self, key: str, desc: str):
        data = DrawerShortcut(
            key=key,
            desc=desc
        )
        self._shortcuts.append(data)
        return data

    def set_active(self, key: str, value: bool):
        for i in self._shortcuts:
            if key != i.key: continue
            i.is_active = value

    def draw_shortcut(self, pos: Vector, shortcut: DrawerShortcut):
        font_id = 0
        blf.color(font_id, 1, 1, 1, 1)

        if shortcut.is_active:
            blf.color(font_id, 0, 1, 1, 1)

        blf.position(font_id, pos.x, pos.y, 0)
        blf.size(font_id, self._font_size)
        blf.draw(font_id, shortcut.key)
        size = blf.dimensions(font_id, shortcut.key)

        blf.color(font_id, .8, .8, .8, 1)
        if shortcut.is_active:
            blf.color(font_id, 0, .8, .8, 1)
        blf.position(font_id, pos.x + size[0] + self._padding_x, pos.y, 0)
        blf.size(font_id, self._font_size)
        blf.draw(font_id, shortcut.desc)

    def _handle(self):
        for index, i in enumerate(self._shortcuts):
            self.draw_shortcut(
                Vector((self._padding_x * .5, (self._padding_y + self._font_size) * index + self._padding_y)), i)

    def activate(self):
        if self._draw_id is not None:
            return

        self._draw_id = bpy.types.SpaceView3D.draw_handler_add(self._handle, (), 'WINDOW', 'POST_PIXEL')

    def deactivate(self):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_id, 'WINDOW')
            self._draw_id = None
        except Exception:
            pass

    def __del__(self):
        self.deactivate()

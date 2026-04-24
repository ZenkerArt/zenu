from dataclasses import dataclass
from typing import Any

import bpy

from ..utils import ObjectTypes, object_filter


def base_draw(self: 'BaseSocketType', layout: bpy.types.UILayout):
    if self.hide_value or not hasattr(self, 'value'):
        layout.label(text=self.human_name)
        return

    row = layout.row()

    if not self.is_linked or self.is_output:
        row.prop(self, "value", text='', placeholder=self.human_name)
    else:
        val = self.links[0].from_socket.value
        if val is not None:
            row.label(text=f'String: {val.name}')



class BaseSocketType(bpy.types.NodeSocket):
    bl_idname = "TestSocketType"
    bl_label = "Test Socket Type"
    map_type: Any = None

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout, node: bpy.types.Node, text: str):
        pass

    @property
    def human_name(self):
        return self.name.title()

    @staticmethod
    def poll(node, link):
        from_socket = link.from_socket
        to_socket = link.to_socket

        if type(from_socket) == AnySocketType:
            return True

        return type(from_socket) == type(to_socket)


class TestSocketType(BaseSocketType):
    bl_idname = "TestSocketType"
    bl_label = "Test Socket Type"

    value: bpy.props.FloatProperty(default=0.0)

    def draw(self, context, layout, node, text):
        layout.prop(self, "value", text=text)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.2, 1.0)




class ObjectSocketType(BaseSocketType):
    bl_idname = "ObjectInput"
    bl_label = "Object Input"
    map_type = bpy.types.Object
    filter_type: bpy.props.StringProperty(default=ObjectTypes.NONE)
    value: bpy.props.PointerProperty(type=bpy.types.Object, poll=object_filter)

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.5, 1.0)


class StringTypeSocket(BaseSocketType):
    bl_idname = "StringInput"
    bl_label = "Object Input"
    map_type = str
    value: bpy.props.StringProperty()

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.5, 1.0)


class MaskTypeSocket(BaseSocketType):
    bl_idname = "MaskInput"
    bl_label = "Mask Input"
    map_type = str
    value = None

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.8, 0.8, 0.5, 1.0)


@dataclass
class CharacterEquipmentData:
    name: str
    armature: bpy.types.Object
    object: bpy.types.Object


class CharacterEquipTypeSocket(BaseSocketType):
    bl_idname = "CharacterEquip"
    bl_label = "Character Equipment"
    map_type = CharacterEquipmentData

    def draw(self, context, layout, node, text):
        base_draw(self, layout)

    def draw_color(self, context, node):
        return (0.8, 0.4, 0.1, 1.0)


class AnySocketType(BaseSocketType):
    bl_idname = "AnyInput"
    bl_label = "Any Input"
    map_type = Any
    value = None

    @staticmethod
    def poll(node, link):
        return True

    def draw(self, context, layout, node, text):
        layout.label(text=self.name.title())

    def draw_color(self, context, node):
        return (1, 1, 1, 1.0)


sockets = [
    TestSocketType,
    ObjectSocketType,
    AnySocketType,
    StringTypeSocket,
    CharacterEquipTypeSocket,
    MaskTypeSocket
]

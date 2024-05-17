import inspect
from dataclasses import dataclass
from typing import Callable

import bpy
import mathutils
from mathutils import Vector
from .. import FunctionNodeResult, FunctionNode, socket_store, NodeContext


def add(a: Vector, b: Vector):
    return a + b


def subtract(a: Vector, b: Vector):
    return a - b


def multiply(a: Vector, b: Vector):
    return Vector((a.x * b.x, a.y * b.y, a.z * b.z))


def divide(a: Vector, b: Vector):
    return Vector((a.x / b.x, a.y / b.y, a.z / b.z))


def scale(a: Vector, scale: float):
    return a * scale


math_functions = {
    'ADD': add,
    'SUBTRACT': subtract,
    'MULTIPLY': multiply,
    'DIVIDE': divide,
    'SCALE': scale
}


@dataclass
class GetBoneResult(FunctionNodeResult):
    bone: bpy.types.PoseBone


class ZENU_ND_vector(FunctionNode):
    bl_label = 'Vector'

    def call(self, x: float, y: float, z: float) -> Vector:
        # print(x, y, z)
        return Vector((x, y, z))


def math_enum(self, context):
    return tuple((key, key.title(), '') for key, func in math_functions.items())


def update(self, context):
    self.update_enum()


class ZENU_ND_vector_math(FunctionNode):
    bl_label = 'Vector Math'
    enum: bpy.props.EnumProperty(items=math_enum, update=update)

    def init(self, context: bpy.types.Context):
        self.output('NodeSocketVector', 'Result')

        self.inputs.clear()
        self.create_inputs_from_function(math_functions[self.enum])

    def create_inputs_from_function(self, func: Callable):
        for key, typ in inspect.get_annotations(func).items():
            if key == 'return':
                continue

            socket_name = socket_store.get_socket_name_by_type(typ).socket_name

            self.input(socket_name, key)

    def update_enum(self):
        self.inputs.clear()
        self.create_inputs_from_function(math_functions[self.enum])

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        layout.prop(self, 'enum', text='')

    def execute(self, context: bpy.types.Context, node_context: NodeContext):
        return math_functions[self.enum](**node_context.props)


nodes = (
    ZENU_ND_vector,
    ZENU_ND_vector_math
)

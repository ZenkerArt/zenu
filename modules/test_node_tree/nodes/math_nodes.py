import inspect
import math
from typing import Callable

import bpy
from .. import FunctionNode, BaseNode, NodeContext, socket_store


def add(a: float, b: float):
    return a + b


def subtract(a: float, b: float):
    return a - b


def multiply(a: float, b: float):
    return a * b


def divide(a: float, b: float):
    return a / b


def sin(value: float):
    return math.sin(value)


def cos(value: float):
    return math.cos(value)


math_functions = {
    'ADD': add,
    'SUBTRACT': subtract,
    'MULTIPLY': multiply,
    'DIVIDE': divide,
    'SIN': sin,
    'COS': cos,
}


def math_enum(self, context):
    return tuple((key, key.title(), '') for key, func in math_functions.items())


def update(self, context):
    self.update_enum()


class ZENU_ND_math(FunctionNode):
    bl_label = 'Math'
    enum: bpy.props.EnumProperty(items=math_enum, update=update)

    def init(self, context: bpy.types.Context):
        self.output('NodeSocketFloat', 'Result')

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
    ZENU_ND_math,
)

from cProfile import label
import inspect
import re
from typing import Any
import bpy

CamelCase_to_snake_case = re.compile(
    r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def convert_name(name: str):
    return CamelCase_to_snake_case.sub('_', name).lower()


class ActionOperator:
    bl_label: str = ''
    bl_options = {'UNDO'}
    _enum_func = {}
    _func_enum = {}

    @classmethod
    def bl_idname(cls):
        return f'ZENU_OT_{convert_name(cls.__name__)}'

    @classmethod
    def get_action(cls, method: Any) -> str:
        return cls._func_enum[method]

    @classmethod
    def draw_action(cls, layout: bpy.types.UILayout, method: Any, text: str = None, icon: str = 'NONE'):
        if text is None:
            text = cls.get_action(method).title()
        
        op = layout.operator(cls.bl_idname(), text=text, icon=icon)
        op.action = cls.get_action(method)
        return op

    @classmethod
    def gen_op(cls):
        methods = inspect.getmembers(cls, predicate=inspect.isfunction)
        actions = {}
        enum = []
        enum_func = {}
        func_enum = {}

        properties = {}
        for key, value in cls.__annotations__.items():
            if type(value).__name__ == '_PropertyDeferred':
                properties[key] = value

        for name, method in methods:
            if name.startswith('action'):
                actions[name] = method
                s = name.split('_')
                s.pop(0)

                action_name = ' '.join(s).title()
                action_id = '_'.join(s).upper()
                enum_func[action_id] = method
                func_enum[method] = action_id
                enum.append((
                    action_id, action_name, ''
                ))
        cls._enum_func = enum_func
        cls._func_enum = func_enum

        def execute(self, context: bpy.types.Context):
            enum_func[self.action](self, context)
            return {'FINISHED'}

        data = {
            'bl_idname': f'zenu.{convert_name(cls.__name__)}',
            # 'bl_label': cls.bl_label,
            # 'bl_options': cls.bl_options,
            '__annotations__': {
                'action': bpy.props.EnumProperty(items=enum),
                **properties
            },
            # **actions,
            'execute': execute
        }

        new_cls = type(cls.bl_idname(), (bpy.types.Operator, cls), data)

        return new_cls

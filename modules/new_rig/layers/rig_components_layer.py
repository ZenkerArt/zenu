from typing import Type, TypeVar

import bpy

from ..rig_lib import RigLayer, RigComponent, RigContext
T = TypeVar('T')


class RigComponentsLayer(RigLayer):
    _components: list[Type[RigComponent]]
    _components_execute: list[Type[RigComponent]]

    def __init__(self, components: list[Type[RigComponent]]):
        super().__init__()
        self._components = components
        self._components_execute = []

    @property
    def components(self):
        return self._components

    def get_comp(self, comp: Type[T]) -> T:
        for i in self._components_execute:
            if isinstance(i, comp):
                return i

    def execute(self, context: RigContext):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = context.new_armature
        context.new_armature.select_set(True)

        self._components_execute.clear()

        for comp in self._components:
            self._components_execute.append(comp())

        for i in self._components_execute:
            edit_args = context.deps.get_deps_for_func(i.execute_edit)
            pose_args = context.deps.get_deps_for_func(i.execute_pose)
            obj_args = context.deps.get_deps_for_func(i.execute_object)

            i.armature_obj = context.new_armature

            bpy.ops.object.mode_set(mode='OBJECT')
            i.execute_object(**obj_args)
            bpy.ops.object.mode_set(mode='EDIT')
            i.execute_edit(**edit_args)
            bpy.ops.object.mode_set(mode='POSE')
            i.execute_pose(**pose_args)

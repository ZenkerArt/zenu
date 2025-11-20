from collections import defaultdict
from typing import Type

import bpy
from ..rig_lib import RigBone, RigComponent, RigContext, RigLayer
from .rig_components_layer import RigComponentsLayer

class BoneCollectorLayer(RigLayer):
    _type_bones: dict[Type[RigComponent], list[str]]
    _arm: bpy.types.Object

    def __init__(self):
        super().__init__()

        self._type_bones = defaultdict(list)

    def execute(self, context: RigContext, components_layer: RigComponentsLayer):
        self._arm = context.new_armature
        
        for bone in context.new_arm.bones:
            props = bone.zenu_rig_component_props
            for i in components_layer.components:
                if props.component_id == str(i.get_n_id()):
                    self._type_bones[i].append(bone.name)

    def get_bones_by_type(self, tp: RigComponent):
        if tp.__class__ == type:
            return self._type_bones.get(tp)
        
        return self._type_bones.get(type(tp))
    
    def get_edit_bones_by_type(self, tp: RigComponent):
        return tuple(self._arm.data.edit_bones[i] for i in self.get_bones_by_type(tp))
    
    def get_rig_bones_by_type(self, tp: RigComponent):# -> tuple:# -> tuple:
        try:
            return tuple(RigBone(self._arm, i) for i in self.get_bones_by_type(tp))
        except TypeError:
            return []

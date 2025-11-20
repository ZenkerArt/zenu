from collections import defaultdict
from typing import Type

import bpy
from ..rig_lib.bone_utils import clear_bone_collection
from ..rig_lib import RigBone, RigComponent, RigContext, RigLayer
from .rig_components_layer import RigComponentsLayer


class BoneCollectionLayer(RigLayer):
    def __init__(self):
        super().__init__()

        self._type_bones = defaultdict(list)

    def get_collection(self, name: str):
        arm = self.context.new_arm
        
        coll = arm.collections_all.get(name)
        if coll is None:
            coll = arm.collections.new(name)
        
        return coll
    
    def add_parent_collection(self, rig_bone: RigBone, prefix: str = '', postfix: str = ''):
        coll = rig_bone.edit.collections[0]
        
        new_coll = self.get_collection(f'{prefix}{coll.name}{postfix}')
        
        new_coll.parent = coll
        
        return new_coll
    
    def add_to_deform(self, rig_bone: RigBone):
        deform = self.get_collection('Deform')
        b = rig_bone.edit
        
        clear_bone_collection(b)
        deform.assign(b)
    
    def add_to_mechanic(self, rig_bone: RigBone):
        deform = self.get_collection('Mechanic')
        b = rig_bone.edit
        
        clear_bone_collection(b)
        deform.assign(b)

    def execute(self, context: RigContext, components_layer: RigComponentsLayer):
        pass

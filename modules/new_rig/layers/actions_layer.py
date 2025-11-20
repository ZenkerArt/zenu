from collections import defaultdict
import math
from typing import Type

import bpy
from ..action_list import rig_action_list
from ..rig_lib import RigBone, RigComponent, RigContext, RigLayer
from ..rig_lib.bone_utils import bone_get_side
from .rig_components_layer import RigComponentsLayer
from ..builtin_components import ActionControl


class ActionsLayer(RigLayer):
    _type_bones: dict[Type[RigComponent], list[str]]
    _arm: bpy.types.Object

    def __init__(self):
        super().__init__()

        self._type_bones = defaultdict(list)

    def apply_to(self, prop, context: RigContext, main_bone):
        action: bpy.types.Action = prop.action
        subtype: str = ActionControl.get_prop_value(main_bone, 'subtype')
        invert: bool = ActionControl.get_prop_value(main_bone, 'invert')
        side = bone_get_side(main_bone.name)
        
        fm = set()
        start_frame = math.inf
        end_frame = -math.inf

        for curve in action.fcurves.values():
            curve: bpy.types.FCurve
            f_min, f_max = curve.range()
            if f_min < start_frame:
                
                start_frame = f_min

            if f_max > end_frame:
                end_frame = f_max
            
            bone_name = curve.data_path.split('"')[1]
            if prop.mirror:
                if side.lower() == bone_get_side(bone_name).lower():
                    fm.add(bone_name)
            else:
                fm.add(bone_name)
        
        for i in fm:
            bone: bpy.types.PoseBone = self.context.new_armature.pose.bones[i]
            animation_action: bpy.types.Action = prop.action

            action: bpy.types.ActionConstraint = bone.constraints.new(
                'ACTION')
            action.action = animation_action

            action.frame_end = int(end_frame)
            action.frame_start = int(start_frame)

            if subtype == '1D':
                min1d: float = ActionControl.get_prop_value(main_bone, 'd1_min')
                max1d: float = ActionControl.get_prop_value(main_bone, 'd1_max')
                action.target_space = 'LOCAL'

                action.target = context.new_armature
                action.subtarget = main_bone.name
                action.transform_channel = 'LOCATION_Y'
                action.target_space = 'LOCAL'
                    
                if invert:
                    action.min = max1d
                    action.max = min1d
                else:
                    action.min = min1d
                    action.max = max1d
        

    def execute(self, context: RigContext, components_layer: RigComponentsLayer):
        bpy.ops.object.mode_set(mode='POSE')
        for prop in rig_action_list.prop_list:
            action: bpy.types.Action = prop.action
            if action is None:
                continue
            
            main_bone = context.new_armature.pose.bones[prop.bone]
            
            self.apply_to(prop, context, main_bone)
            
            
            if prop.mirror:
                main_bone = context.new_armature.pose.bones[prop.mirror_bone]
                self.apply_to(prop, context, main_bone)

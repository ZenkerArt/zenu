from collections import defaultdict
from dataclasses import dataclass, field
import math
from typing import Any, Type, TypeAlias
import typing

import bpy
from bpy_extras import anim_utils
from ..action_list import rig_action_list
from ..rig_lib import RigBone, RigComponent, RigContext, RigLayer
from ..rig_lib.bone_utils import bone_get_side
from .rig_components_layer import RigComponentsLayer
from ..builtin_components import ActionControl

Coords: TypeAlias = typing.Literal[
    "LOCATION_X",
    "LOCATION_Y",
    "LOCATION_Z",
    "ROTATION_X",
    "ROTATION_Y",
    "ROTATION_Z",
    "SCALE_X",
    "SCALE_Y",
    "SCALE_Z",
]


def constraint_to_top(bone: bpy.types.PoseBone, const: bpy.types.Constraint):
    for index, constraint in enumerate(bone.constraints):
        if const.name == constraint.name:
            bone.constraints.move(index, 0)


@dataclass
class AnimationActionSlotWrapper:
    owner: 'AnimationActionWrapper'
    raw: Any
    start_frame: float = math.inf
    end_frame: float = -math.inf
    bones: set[str] = field(default_factory=set)

    def get_bones_by_side(self, bone_name: str):
        side = bone_get_side(bone_name)

        return tuple(bone for bone in self.bones if side.lower() == bone_get_side(bone).lower())


class AnimationActionWrapper:
    _action: bpy.types.Action
    _bones: set[str]

    def __init__(self, action: bpy.types.Action):
        self._action = action

    @property
    def raw(self):
        return self._action

    def get_slot(self, slot):
        self._bones = set()
        wrap_slot = AnimationActionSlotWrapper(
            owner=self,
            raw=slot
        )

        fcurves = anim_utils.action_get_channelbag_for_slot(
            self._action, slot).fcurves

        for curve in fcurves.values():
            curve: bpy.types.FCurve
            f_min, f_max = curve.range()
            if f_min < wrap_slot.start_frame:

                wrap_slot.start_frame = f_min

            if f_max > wrap_slot.end_frame:
                wrap_slot.end_frame = f_max

            bone_name = curve.data_path.split('"')[1]
            wrap_slot.bones.add(bone_name)

        return wrap_slot

    def get_slot_by_index(self, index: int):
        return self.get_slot(self.raw.slots[index])


class ActionConstraintWrapper:
    _action_constraint: bpy.types.ActionConstraint
    _action_animation: AnimationActionWrapper

    def __init__(self, bone: bpy.types.PoseBone, action: AnimationActionWrapper):
        self._action_constraint = bone.constraints.new('ACTION')
        self._action_animation = action
        
        constraint_to_top(bone, self._action_constraint)

    def set_action_range(self, fmin: float, fmax: float, coord: Coords):
        self._action_constraint.min = fmin
        self._action_constraint.max = fmax

        self.set_local(coord)

    def set_target(self, obj: bpy.types.Object, bone_name: str):
        self._action_constraint.target = obj
        self._action_constraint.subtarget = bone_name

    def set_local(self, coord: Coords):
        self._action_constraint.target_space = 'LOCAL'
        self._action_constraint.transform_channel = coord

    def set_slot(self, slot: AnimationActionSlotWrapper):
        self._action_constraint.action = slot.owner.raw
        self._action_constraint.action_slot = slot.raw

        self._action_constraint.frame_end = int(slot.end_frame)
        self._action_constraint.frame_start = int(slot.start_frame)


class ActionsLayer(RigLayer):
    _type_bones: dict[Type[RigComponent], list[str]]
    _arm: bpy.types.Object

    def __init__(self):
        super().__init__()

        self._type_bones = defaultdict(list)

    def get_bone(self, bone_name: str):
        return self.context.new_armature.pose.bones[bone_name]

    def apply_1d(self, context: RigContext, main_bone, prop, coord: Coords = 'LOCATION_Y'):
        invert: bool = ActionControl.get_prop_value(main_bone, 'invert')

        action = AnimationActionWrapper(prop.action)

        slot = action.get_slot_by_index(0)

        bones = slot.bones

        if prop.mirror:
            bones = slot.get_bones_by_side(main_bone.name)

        for bone_name in bones:
            bone: bpy.types.PoseBone = self.context.new_armature.pose.bones.get(
                bone_name)

            if bone is None:
                continue

            constraint = ActionConstraintWrapper(bone, action)
            constraint.set_slot(slot)

            min1d, max1d = ActionControl.get_1d_range(main_bone)

            constraint.set_target(context.new_armature, main_bone.name)

            if invert:
                constraint.set_action_range(max1d, min1d, coord)
            else:
                constraint.set_action_range(min1d, max1d, coord)

    def apply_radius(self, context: RigContext, main_bone, prop):
        invert: bool = ActionControl.get_prop_value(main_bone, 'invert')

        action = AnimationActionWrapper(prop.action)

        def apply_slot(slot: AnimationActionSlotWrapper, coord: Coords):
            bones = slot.bones

            if prop.mirror:
                bones = slot.get_bones_by_side(main_bone.name)

            for bone_name in bones:
                bone: bpy.types.PoseBone = self.context.new_armature.pose.bones.get(
                    bone_name)

                if bone is None:
                    continue

                constraint = ActionConstraintWrapper(bone, action)
                constraint.set_slot(slot)

                min1d, max1d = ActionControl.get_radius_range(main_bone)

                constraint.set_target(context.new_armature, main_bone.name)

                if invert:
                    constraint.set_action_range(max1d, min1d, coord)
                else:
                    constraint.set_action_range(min1d, max1d, coord)

        slot_x = action.get_slot_by_index(0)

        apply_slot(slot_x, 'LOCATION_X')

        try:
            slot_y = action.get_slot_by_index(1)
            apply_slot(slot_y, 'LOCATION_Y')
        except IndexError:
            pass

    def execute(self, context: RigContext, components_layer: RigComponentsLayer):
        bpy.ops.object.mode_set(mode='POSE')
        for prop in rig_action_list.prop_list:
            action: bpy.types.Action = prop.action
            if action is None:
                continue

            main_bone = context.new_armature.pose.bones[prop.bone]
            subtype: str = ActionControl.get_prop_value(main_bone, 'subtype')

            if subtype == '1D':
                self.apply_1d(context, main_bone, prop)
                if prop.mirror:
                    self.apply_1d(
                        context,
                        context.new_armature.pose.bones[prop.mirror_bone],
                        prop)

            if subtype == 'RADIUS':
                self.apply_radius(context, main_bone, prop)
                if prop.mirror:
                    self.apply_radius(
                        context,
                        context.new_armature.pose.bones[prop.mirror_bone],
                        prop)

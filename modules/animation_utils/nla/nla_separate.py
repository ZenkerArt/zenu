import random
import re
from dataclasses import dataclass, field
from typing import Optional

import bpy
from mathutils import Vector
from ....utils import exit_from_nla, nla_pushdown, nla_duplicate
from ....base_panel import BasePanel

RE_BONE_NAME = re.compile(r'pose.bones\["(.*)"]')


@dataclass
class Channel:
    data_path: str
    index: int
    group: str
    select: bool
    curve: bpy.types.FCurve
    modifiers: list[bpy.types.FModifier] = field(default_factory=list)
    keyframes: list[bpy.types.Keyframe] = field(default_factory=list)
    bone_name: Optional[str] = None


def get_active_nla_strip(obj: bpy.types.Object):
    nla = None
    for i in obj.animation_data.nla_tracks.active.strips:
        if i.active:
            nla = i

    return nla


def copy_keyframe(src: bpy.types.Keyframe, dst: bpy.types.Keyframe):
    dst.handle_left = src.handle_left
    dst.handle_right = src.handle_right
    dst.handle_left_type = src.handle_left_type
    dst.handle_right_type = src.handle_right_type
    dst.interpolation = src.interpolation


# class ZENU_OT_nla_separate(bpy.types.Operator):
#     bl_label = 'Separate'
#     bl_idname = 'zenu.nla_separate'
#     bl_options = {'UNDO', 'REGISTER'}
#     only_selected_bone: bpy.props.BoolProperty(name='Only Selected Bone', default=True)
#     only_selected_channel: bpy.props.BoolProperty(name='Only Selected Channel', default=False)
#     remove_separated: bpy.props.BoolProperty(name='Remove Separated', default=True)
#     with_nla_props: bpy.props.BoolProperty(name='With Nla Properties', default=True)
#     copy_modifiers: bpy.props.BoolProperty(name='Copy Modifiers', default=True)
#
#     def serlialize_fcurves(self, fcurves: bpy.types.ActionFCurves):
#         channels = []
#         for curve in fcurves:
#             bone_name = re.findall(RE_BONE_NAME, curve.data_path)
#
#             if bone_name:
#                 bone_name = bone_name[0]
#             else:
#                 bone_name = None
#             # curve.modifiers.
#             channel = Channel(
#                 data_path=curve.data_path,
#                 index=curve.array_index,
#                 group=curve.group.name,
#                 select=curve.select,
#                 bone_name=bone_name,
#                 curve=curve
#             )
#             channel.modifiers = [i for i in curve.modifiers]
#             channel.keyframes = [frame for frame in curve.keyframe_points]
#             channels.append(channel)
#
#         return channels
#
#     def execute(self, context: bpy.types.Context):
#         if context.selected_pose_bones is None:
#             self.report({'WARNING'}, 'Bone Not Selected.')
#             return {'CANCELLED'}
#
#         if context.active_action is None:
#             self.report({'WARNING'}, 'Action Empty.')
#             return {'CANCELLED'}
#
#         action = bpy.data.actions.new(context.active_action.name)
#
#         prev_fcurves = context.active_action.fcurves
#         prev_nla = get_active_nla_strip(context.active_object)
#
#         fcurve = self.serlialize_fcurves(prev_fcurves)
#
#         exit_from_nla(context.active_object)
#
#         selected_bones = [bone.name for bone in context.selected_pose_bones]
#
#         for i in fcurve:
#             if not i.select and self.only_selected_channel: continue
#             if i.bone_name not in selected_bones and self.only_selected_bone: continue
#
#             if self.remove_separated:
#                 prev_fcurves.remove(i.curve)
#
#             fcurve = action.fcurves.new(data_path=i.data_path, index=i.index, action_group=i.group)
#
#             if self.copy_modifiers:
#                 for mod in i.modifiers:
#                     if mod.type == 'CYCLES':
#                         fcurve.modifiers.new(mod.type)
#
#             for key in i.keyframes:
#                 keyframe = fcurve.keyframe_points.insert(key.co.x, key.co.y)
#                 copy_keyframe(keyframe, key)
#         context.active_object.animation_data.action = action
#
#         if not self.with_nla_props:
#             return {'FINISHED'}
#
#         nla_pushdown(context.active_object)
#
#         nla_strip = get_active_nla_strip(context.active_object)
#         nla_strip.repeat = prev_nla.repeat
#         nla_strip.use_sync_length = prev_nla.use_sync_length
#         nla_strip.scale = prev_nla.scale
#         nla_strip.frame_start = prev_nla.frame_start
#         nla_strip.frame_end = prev_nla.frame_end
#         nla_strip.blend_in = prev_nla.blend_in
#         nla_strip.blend_out = prev_nla.blend_out
#         nla_strip.blend_type = prev_nla.blend_type
#         nla_strip.extrapolation = prev_nla.extrapolation
#         nla_strip.use_reverse = prev_nla.use_reverse
#         nla_strip.use_animated_time_cyclic = prev_nla.use_animated_time_cyclic
#         nla_strip.use_animated_time = prev_nla.use_animated_time
#
#         def get_fcurve(strip: bpy.types.NlaStrip):
#             for i in strip.fcurves:
#                 if i.data_path != 'strip_time': continue
#
#                 return i
#
#         prev_time = get_fcurve(prev_nla)
#         time = get_fcurve(nla_strip)
#
#         for keyframe in prev_time.keyframe_points:
#             keyframe_dst = time.keyframe_points.insert(keyframe.co.x, keyframe.co.y)
#             copy_keyframe(keyframe, keyframe_dst)
#
#         return {'FINISHED'}


class ZENU_OT_nla_separate(bpy.types.Operator):
    bl_label = 'Separate'
    bl_idname = 'zenu.nla_separate'
    bl_options = {'UNDO', 'REGISTER'}
    only_selected_bone: bpy.props.BoolProperty(name='Only Selected Bone', default=True)
    only_selected_channel: bpy.props.BoolProperty(name='Only Selected Channel', default=False)
    remove_separated: bpy.props.BoolProperty(name='Remove Separated', default=True)

    def execute(self, context: bpy.types.Context):
        if context.selected_pose_bones is None:
            self.report({'WARNING'}, 'Bone Not Selected.')
            return {'CANCELLED'}

        if context.active_action is None:
            self.report({'WARNING'}, 'Action Empty.')
            return {'CANCELLED'}

        obj = context.active_object
        old_nla = get_active_nla_strip(obj)
        old_action = old_nla.action

        exit_from_nla(obj)
        obj.animation_data.nla_tracks.new()
        nla_duplicate(obj)

        new_nla = get_active_nla_strip(obj)
        new_action = new_nla.action
        selected_bones = [bone.name for bone in context.selected_pose_bones]

        for curve in new_action.fcurves:
            bone_name = re.findall(RE_BONE_NAME, curve.data_path)
            if bone_name:
                bone_name = bone_name[0]
            else:
                bone_name = None

            selected_channel = curve.select and self.only_selected_channel
            selected_bones_ = bone_name in selected_bones and self.only_selected_bone

            if selected_channel or selected_bones_: continue
            new_action.fcurves.remove(curve)

        if not self.remove_separated:
            return {'FINISHED'}

        for curve in old_action.fcurves:
            bone_name = re.findall(RE_BONE_NAME, curve.data_path)
            if bone_name:
                bone_name = bone_name[0]
            else:
                bone_name = None

            selected_channel = curve.select and self.only_selected_channel
            selected_bones_ = bone_name in selected_bones and self.only_selected_bone

            if selected_channel or selected_bones_:
                old_action.fcurves.remove(curve)

        return {'FINISHED'}


def draw(self, context: bpy.types.Context):
    layout: bpy.types.UILayout = self.layout
    layout.operator(ZENU_OT_nla_separate.bl_idname)


class ZENU_PT_nla_separate_de(BasePanel):
    bl_label = 'NLA Separate'
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


class ZENU_PT_nla_separate_ge(BasePanel):
    bl_label = 'NLA Separate'
    bl_space_type = 'GRAPH_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_nla_separate_de,
    ZENU_PT_nla_separate_ge,
    ZENU_OT_nla_separate
))


def register():
    reg()


def unregister():
    unreg()

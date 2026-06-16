from dataclasses import dataclass
import os

from .utils import export_animinfo
from .action_list_export import action_list_export
from .models import ActionExport
from .models import ActionExportObject
from ..base_operator.action_operator import ActionOperator
from ...utils import get_modifier
import bpy


def remove_bone_by_mask(target_obj: bpy.types.Object, bones_mask: list[str] = None):
    obj = target_obj.copy()
    obj.data = obj.data.copy()
    bones_mask = bones_mask or []
    data: bpy.types.Armature = obj.data

    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj

    for bone in obj.pose.bones:
        constraints = list(bone.constraints).copy()
        
        for const in constraints:
            bone.constraints.remove(const)

        const: bpy.types.CopyTransformsConstraint = bone.constraints.new(
            'COPY_TRANSFORMS')
        const.target = target_obj
        const.subtarget = bone.name

    bpy.ops.object.mode_set(mode='POSE')
    # bpy.ops.object.select_all('DESELECT')
    # for bone in obj.pose.bones:
    # bone.select = bone.name in bones_mask
    # bpy.ops.nla.bake(only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end)
    return obj


@dataclass
class ApplyMaskUndo:
    new_obj: bpy.types.Object
    target_obj: bpy.types.Object
    modifiers: list[bpy.types.ArmatureModifier]

    def undo(self):
        for mod in self.modifiers:
            mod.object = self.target_obj

        data = self.new_obj.data
        data_name = data.name
        obj_name = self.new_obj.name
        bpy.data.objects.remove(self.new_obj)
        bpy.data.armatures.remove(data)

        self.target_obj.name = obj_name
        try:
            self.target_obj.data.name = data_name
        except Exception:
            pass


class ActionExportOps(ActionOperator):
    bl_label = 'Action Export'
    mute: bpy.props.BoolProperty(default=True)
    name: bpy.props.StringProperty()
    slot: bpy.props.StringProperty()
    item_uuid: bpy.props.StringProperty()

    def get_slot(self, action: bpy.types.Action, slot_name: str):
        for sl in action.slots:
            if sl.name_display == slot_name:
                return sl

        return None

    def get_objects(self, item: ActionExport) -> list[bpy.types.Object]:
        data = item.load_anim_info()
        delete_list = []
        objs = []
        for obj_name in data.objects:
            try:
                objs.append(bpy.data.objects[obj_name])
            except Exception:
                delete_list.append(obj_name)
                continue

        for obj_name in delete_list:
            del data.objects[obj_name]

        item.data = data.to_dict()
        return objs

    def apply_bones_mask(self, target_obj: bpy.types.Object, action: bpy.types.Action):
        data: bpy.types.Armature = target_obj.data
        bones_mask = []
        for curve in action.fcurves:
            try:
                bone_name = curve.data_path.replace(
                    'pose.bones["', '').split('"]')[0]
                data.bones[bone_name]
                bones_mask.append(bone_name)
            except Exception:
                print('[Bake Only Selected] Error with', curve)

        new_obj = remove_bone_by_mask(target_obj, bones_mask)

        modifiers = []

        for objk in bpy.data.objects:
            for i in objk.modifiers:
                if not isinstance(i, bpy.types.ArmatureModifier):
                    continue

                if hasattr(i, 'object') and i.object == target_obj:
                    modifiers.append(i)

        for mod in modifiers:
            mod.object = new_obj

        name = target_obj.name
        name_data = target_obj.data.name

        target_obj.name = f'{name}_tmp'
        try:
            target_obj.data.name = f'{name_data}_tmp'
        except Exception:
            pass

        new_obj.name = name
        new_obj.data.name = name_data

        return ApplyMaskUndo(
            new_obj=new_obj,
            modifiers=modifiers,
            target_obj=target_obj
        )

    def action_bake_only_animated(self, context: bpy.types.Context):
        new_obj = self.apply_bones_mask(
            context.active_object, context.active_object.animation_data.action)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        new_obj.select_set(True)
        bpy.context.view_layer.objects.active = new_obj

        bpy.ops.object.mode_set(mode='POSE')

    def action_toggle(self, context: bpy.types.Context):
        item = action_list_export.active
        data = item.load_anim_info()
        name: str = self.name

        if name in data.objects:
            del data.objects[name]
        else:
            data.objects[name] = ActionExportObject(slot=self.slot).to_dict()

        item.data = data.to_dict()

    def create_edit_data(self):
        return {
            'scene_name': bpy.context.scene.name,
            'animation': {}
        }

    def default_export_prepare(self, item: ActionExport):
        data = item.load_anim_info()
        action: bpy.types.Action = item.action
        edit_data = self.create_edit_data()

        for obj in self.get_objects(item):
            mask = None
            name = obj.name
            if item.use_bake_only_animated:
                mask = self.apply_bones_mask(obj, action)
                mask.new_obj.select_set(True)
                name = mask.new_obj.name

                mask.new_obj.animation_data.action_blend_type = 'REPLACE'
                mask.new_obj.animation_data.action = action
                mask.new_obj.animation_data.action_slot = self.get_slot(
                    action, data.get_object(name).slot)
            else:
                obj.select_set(True)

            edit_data['animation'][obj] = {
                'action': obj.animation_data.action,
                'blend_type': obj.animation_data.action_blend_type,
                'undo_mask': mask
            }

            obj.animation_data.action_blend_type = 'REPLACE'
            obj.animation_data.action = action
            obj.animation_data.action_slot = self.get_slot(
                action, data.get_object(name).slot)

            if item.export_mesh:
                for i in bpy.data.objects:
                    arm_mod: bpy.types.ArmatureModifier = get_modifier(
                        i, bpy.types.ArmatureModifier)
                    if arm_mod is None:
                        continue

                    if arm_mod.object == obj:
                        i.select_set(True)

            # if item.use_bake_only_animated:

        return edit_data

    def additive_export_prepare(self, item: ActionExport):
        data = item.load_anim_info()
        action: bpy.types.Action = item.action
        edit_data = self.create_edit_data()

        bpy.context.scene.name = item.name

        for obj in self.get_objects(item):
            strips = {}
            edit_data['animation'][obj] = {
                'action': obj.animation_data.action,
                'strips': strips,
                'blend_type': obj.animation_data.action_blend_type
            }
            obj.animation_data.action_blend_type = 'COMBINE'
            obj.select_set(True)

            obj.animation_data.action = action
            obj.animation_data.action_slot = self.get_slot(
                action, data.get_object(obj.name).slot)

            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    strips[strip] = {'mute': strip.mute,
                                     'frame_end': strip.frame_end}
                    if strip.action != item.action_additive:
                        strip.mute = True
                    else:
                        strip.mute = False
                        strip.frame_end = 0

            if item.export_mesh:
                for i in bpy.data.objects:
                    arm_mod: bpy.types.ArmatureModifier = get_modifier(
                        i, bpy.types.ArmatureModifier)
                    if arm_mod is None:
                        continue

                    if arm_mod.object == obj:
                        i.select_set(True)

        return edit_data

    def action_export(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)

        data = item.load_anim_info()
        action: bpy.types.Action = item.action
        mode = bpy.context.active_object.mode
        prev_range = (context.scene.frame_start, context.scene.frame_end)
        active_object = context.active_object

        context.scene.frame_start = int(action.frame_start)
        context.scene.frame_end = int(action.frame_end)

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        selected_object = list(bpy.context.selected_objects).copy()
        bpy.ops.object.select_all(action='DESELECT')

        export_mode = ''

        if item.use_additive:
            edit_data = self.additive_export_prepare(item)
            export_mode = 'SCENE'
        else:
            edit_data = self.default_export_prepare(item)
            export_mode = 'ACTIVE_ACTIONS'

        filepath = f'{os.path.join(bpy.path.abspath(item.export_path), item.name)}.glb'

        bpy.ops.export_scene.gltf(
            filepath=filepath,
            use_selection=True,
            export_animation_mode=export_mode,
            export_anim_scene_split_object=False,
            export_nla_strips_merged_animation_name=item.name,
            export_image_format='AUTO' if item.export_textures else 'NONE',
            use_renderable=False,
            export_reset_pose_bones=False,
            export_rest_position_armature=False,
        
            export_vertex_color='ACTIVE',
            export_all_vertex_colors=False,
            export_force_sampling=not item.use_bake_only_animated,
            export_apply=item.apply_mods,
            # export_def_bones=True
        )

        if item.export_animinfo:
            export_animinfo(item)

        bpy.ops.object.select_all(action='DESELECT')

        for obj, data in edit_data['animation'].items():
            obj.animation_data.action = data['action']
            obj.animation_data.action_blend_type = data['blend_type']
            undo_mask = data.get('undo_mask')

            if undo_mask:
                undo_mask.undo()

            try:
                for strip, strip_data in data['strips'].items():
                    strip.mute = strip_data['mute']
                    strip.frame_end = strip_data['frame_end']
            except KeyError:
                pass

        bpy.context.scene.name = edit_data['scene_name']
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_object:
            obj.select_set(True)
        context.scene.frame_start, context.scene.frame_end = prev_range

        bpy.context.view_layer.objects.active = active_object

        try:
            bpy.ops.object.mode_set(mode=mode)
        except Exception:
            pass
        self.report({'INFO'}, f'Exported to {filepath}')

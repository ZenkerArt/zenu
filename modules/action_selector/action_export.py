from dataclasses import dataclass, field, asdict
import json
import os
import uuid
import bpy

from ...utils import get_modifier

from ..new_rig import ActionOperator

from ..base_ui_list import ZenuUIList
from ...base_panel import BasePanel

def export_animinfo(item: 'ActionExport'):
    filepath = os.path.join(bpy.path.abspath(item.export_path), f'{item.name}.animinfo')
    
    with open(filepath, mode='w') as f:
        data = json.loads(item.trigger_data)
        data['fps'] = bpy.context.scene.render.fps
        data['frames'] = item.action.frame_end - item.action.frame_start
        f.write(json.dumps(data))
    
    return filepath

@dataclass
class ActionExportObject:
    slot: str = ''

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(
                slot=data['slot']
            )
        except Exception:
            return cls()


@dataclass
class ActionExportItem:
    objects: dict[str, ActionExportObject] = field(default_factory=dict)

    def to_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data):
        try:
            obj = json.loads(data)
            return cls(
                objects={key: ActionExportObject.from_dict(
                    value) for key, value in obj['objects'].items()}
            )
        except Exception as e:
            return cls()

    def has_object(self, name: str):
        return name in self.objects

    def get_object(self, name: str):
        return self.objects.get(name)


class ActionExport(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    data: bpy.props.StringProperty()
    uuid: bpy.props.StringProperty()
    export_mesh: bpy.props.BoolProperty()
    export_textures: bpy.props.BoolProperty()
    export_path: bpy.props.StringProperty(subtype='DIR_PATH', options={
                                          'PATH_SUPPORTS_BLEND_RELATIVE'}, default='')
    export_animinfo: bpy.props.BoolProperty()
    apply_mods: bpy.props.BoolProperty()

    use_additive: bpy.props.BoolProperty()
    action_additive: bpy.props.PointerProperty(type=bpy.types.Action)

    trigger_data: bpy.props.StringProperty()
    trigger_edit_mode: bpy.props.BoolProperty(default=False)

    def _on_select(self):
        pass

    def load_anim_info(self):
        return ActionExportItem.from_json(self.data)

    def load_triggers(self):
        return ExportTriggerData.from_json(self.trigger_data)


class ActionExportList(ZenuUIList[ActionExport]):
    name = 'action_export_list'
    _property_group = ActionExport

    def _draw(self, layout, item: ActionExport):
        layout.prop(item, 'name', text='', emboss=False)
        row = layout.row(align=True)

        if item.export_mesh:
            row.label(icon='MESH_CUBE')
        if item.export_textures:
            row.label(icon='TEXTURE')

        op = ActionExportOps.draw_action(
            layout, ActionExportOps.action_export, text='', icon='EXPORT', emboss=False)
        op.item_uuid = item.uuid

    def get_by_id(self, uuid: str):
        for i in self.prop_list:
            if i.uuid == uuid:
                return i

        return

    def add(self):
        item = super().add()
        item.name = 'No Name'
        item.uuid = uuid.uuid4().hex
        item.data = ActionExportItem().to_json()
        return item


action_list_export = ActionExportList()


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

        item.data = data.to_json()
        return objs

    # Convert to op.action = 'back'
    def action_toggle(self, context: bpy.types.Context):
        item = action_list_export.active
        data = item.load_anim_info()
        name: str = self.name

        if name in data.objects:
            del data.objects[name]
        else:
            data.objects[name] = ActionExportObject(slot=self.slot).to_dict()

        item.data = data.to_json()

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
            edit_data['animation'][obj] = {
                'action': obj.animation_data.action
            }

            obj.select_set(True)

            obj.animation_data.action = action
            obj.animation_data.action_slot = self.get_slot(
                action, data.get_object(obj.name).slot)

            if item.export_mesh:
                for i in bpy.data.objects:
                    arm_mod: bpy.types.ArmatureModifier = get_modifier(
                        i, bpy.types.ArmatureModifier)
                    if arm_mod is None:
                        continue

                    if arm_mod.object == obj:
                        i.select_set(True)
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
                'strips': strips
            }

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
            export_apply=item.apply_mods,
            # export_def_bones=True
        )
        
        if item.export_animinfo:
            export_animinfo(item)

        self.report({'INFO'}, f'Exported to {filepath}')

        bpy.ops.object.select_all(action='DESELECT')

        for obj in selected_object:
            obj.select_set(True)

        bpy.context.scene.name = edit_data['scene_name']

        for obj, data in edit_data['animation'].items():
            obj.animation_data.action = data['action']

            try:
                for strip, strip_data in data['strips'].items():
                    strip.mute = strip_data['mute']
                    strip.frame_end = strip_data['frame_end']
            except KeyError:
                pass

        context.scene.frame_start, context.scene.frame_end = prev_range
        try:
            bpy.ops.object.mode_set(mode=mode)
        except Exception:
            pass


@dataclass
class ExportTriggerDataItem:
    frame: int = 0
    name: str = ''

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data['name'],
            frame=data['frame']
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class ExportTriggerData:
    triggers: list[ExportTriggerDataItem] = field(default_factory=list)

    def add_trigger(self, frame: int, name: str):
        self.triggers.append(ExportTriggerDataItem(
            frame=frame,
            name=name
        ))

    def load_markers(self):
        data = self.triggers
        for trigger in data:

            bpy.context.scene.timeline_markers.new(
                name=trigger.name, frame=trigger.frame)

    def save_markers(self):
        self.triggers = []
        markers = bpy.context.scene.timeline_markers

        for marker in markers.values():
            self.add_trigger(
                marker.frame,
                marker.name
            )

    def to_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str):
        try:
            obj = json.loads(data)
            return cls(
                triggers=[ExportTriggerDataItem.from_dict(
                    i) for i in obj['triggers']],
            )
        except Exception as e:

            return cls()


class ActionExportTriggerOps(ActionOperator):
    bl_label = 'Action Export'
    item_uuid: bpy.props.StringProperty()
    frame: bpy.props.IntProperty()
    name: bpy.props.StringProperty()

    def action_start_editing(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)
        trigger_data = item.load_triggers()
        item.trigger_edit_mode = True

        bpy.context.scene.timeline_markers.clear()

        trigger_data.load_markers()

    def action_end_editing(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)
        trigger_data = item.load_triggers()
        item.trigger_edit_mode = False

        trigger_data.save_markers()
        bpy.context.scene.timeline_markers.clear()
        item.trigger_data = trigger_data.to_json()

    def action_remove(self, context: bpy.types.Context):
        for marker in bpy.context.scene.timeline_markers:
            if self.frame == marker.frame and self.name == marker.name:
                bpy.context.scene.timeline_markers.remove(marker)
    
    def action_export(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)
        filepath = export_animinfo(item)
        
        self.report({'INFO'}, f'Exported to {filepath}')


class ZENU_PT_action_export(BasePanel):
    bl_label = 'Action Export'
    bl_parent_id = 'ZENU_PT_action_selector'
    bl_context = ''

    def get_action_slot(self, obj: bpy.types.Object, action: bpy.types.Action):
        if obj.animation_data is None:
            return None

        if obj.animation_data.action != action:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action == action:
                        return strip.action_slot
        else:
            return obj.animation_data.action_slot

        return None

    def draw_export_settings(self, layout: bpy.types.UILayout):
        active_item = action_list_export.active

        header, lay = layout.panel('Settings', default_closed=True)
        header.label(text='Settings')

        if not lay:
            return

        lay.prop(active_item, 'export_mesh',
                 text='Export Mesh', icon='MESH_CUBE')
        lay.prop(active_item, 'export_textures',
                 text='Export Textures', icon='TEXTURE')
        lay.prop(active_item, 'export_animinfo',
                 text='Export AnimInfo', icon='ANIM_DATA')

        lay.prop(active_item, 'apply_mods',
                 text='Apply Modifier', icon='MODIFIER')

        col = lay.column(align=True)
        col.prop(active_item, 'use_additive',
                 text='Additive', icon='ADD')
        if active_item.use_additive:
            col.prop(active_item, 'action_additive',
                     text='', icon='ACTION')

        lay.prop(active_item, 'export_path',
                 text='', icon='EXPORT')

    def draw_trigger(self, layout: bpy.types.UILayout):
        active_item = action_list_export.active

        header, lay = layout.panel('Trigger', default_closed=True)
        header.label(text='Trigger')

        if not lay:
            return

        lay.label(text=active_item.trigger_data)
        lay.label(text=f'{active_item.trigger_edit_mode}')
        if active_item.trigger_edit_mode:
            op = ActionExportTriggerOps.draw_action(
                lay, ActionExportTriggerOps.action_end_editing, text='End Edit', depress=True)
        else:
            op = ActionExportTriggerOps.draw_action(
                lay, ActionExportTriggerOps.action_start_editing, text='Edit')
        
        op.item_uuid = active_item.uuid
        
        op = ActionExportTriggerOps.draw_action(
                lay, ActionExportTriggerOps.action_export, text='Export')

        op.item_uuid = active_item.uuid

        if active_item.trigger_edit_mode:
            for marker in bpy.context.scene.timeline_markers:
                box = lay.box()
                box.label(text=f'Frame {marker.frame}')
                
                col = box.column(align=True)
                row = col.row(align=True)
                op = ActionExportTriggerOps.draw_action(
                    row, ActionExportTriggerOps.action_remove, text='', icon='REMOVE')
                row.prop(marker, 'name', text='')
                col.prop(marker, 'frame', text='')
                op.name = marker.name
                op.frame = marker.frame

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        action_list_export.draw_ui(layout)
        active_item = action_list_export.active

        if active_item is None:
            return

        layout.label(text=active_item.data)
        col = layout.column(align=True)
        col.prop(active_item, 'action', text='')
        op = ActionExportOps.draw_action(
            col, ActionExportOps.action_export, text='Export')

        op.item_uuid = active_item.uuid

        self.draw_export_settings(layout)
        self.draw_trigger(layout)

        action: bpy.types.Action = active_item.action
        data = active_item.load_anim_info()

        col = layout.column()

        for obj in bpy.data.objects:
            has_obj = data.has_object(obj.name)
            action_slot = self.get_action_slot(obj, action)

            if not action_slot and not has_obj:
                continue

            box = col.box()
            row = box.row(align=True)
            row.scale_y = 1.4
            row.label(text=obj.name)
            row.alert = has_obj

            remove_text = ''

            if not action_slot:
                remove_text = 'Object not have action.'

            op = ActionExportOps.draw_action(
                row, ActionExportOps.action_toggle, text=remove_text, icon='REMOVE' if has_obj else 'ADD')
            op.name = obj.name
            try:
                box.label(
                    text=f'Slot: {active_item.load_anim_info().get_object(obj.name).slot}')
            except AttributeError:
                pass

            if action_slot:
                op.slot = action_slot.name_display


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_action_export,
    ActionExportOps.gen_op(),
    ActionExportTriggerOps.gen_op()
))


def register():
    action_list_export.register()
    reg()


def unregister():
    action_list_export.unregister()
    unreg()

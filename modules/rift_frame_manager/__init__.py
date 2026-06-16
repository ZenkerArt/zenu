import os

import bpy

from ..base_ui_list import ZenuUIList
from ..rift_character import get_objects_by_armature
from ...base_panel import RiftBasePanel


def get_actor_objects() -> list[bpy.types.Object]:
    return [a.object for a in rift_actor_list.prop_list if a.object is not None]


def get_key_targets() -> list[bpy.types.Object]:
    targets = get_actor_objects()
    camera = bpy.context.scene.camera
    if camera is not None and camera not in targets:
        targets.append(camera)
    return targets


def key_transform(target):
    target.keyframe_insert(data_path='location')
    if target.rotation_mode == 'QUATERNION':
        target.keyframe_insert(data_path='rotation_quaternion')
    elif target.rotation_mode == 'AXIS_ANGLE':
        target.keyframe_insert(data_path='rotation_axis_angle')
    else:
        target.keyframe_insert(data_path='rotation_euler')
    target.keyframe_insert(data_path='scale')


def key_shapes(mesh: bpy.types.Object):
    key = mesh.data.shape_keys
    if key is None:
        return

    ref = key.reference_key
    for kb in key.key_blocks:
        if ref is not None and kb == ref:
            continue
        kb.keyframe_insert(data_path='value')


def key_character_control(obj: bpy.types.Object):
    data = obj.data
    if not hasattr(data, 'rift_character_control'):
        return

    for path in ('eye_preset', 'mouth_preset', 'eye_open', 'mouth_open'):
        try:
            data.keyframe_insert(data_path=f'rift_character_control.{path}')
        except (RuntimeError, TypeError):
            pass


def insert_key(obj: bpy.types.Object):
    if obj.animation_data is None:
        obj.animation_data_create()

    key_transform(obj)

    if obj.type == 'ARMATURE':
        for bone in obj.pose.bones:
            key_transform(bone)

        key_character_control(obj)

        for linked in get_objects_by_armature(obj):
            key_shapes(linked)


def assign_action(anim_id, action: bpy.types.Action, slot_name: str, id_type: str):
    if anim_id.animation_data is None:
        anim_id.animation_data_create()

    anim_id.animation_data.action = action

    slot = next((s for s in action.slots
                 if s.target_id_type == id_type and s.name_display == slot_name), None)
    if slot is not None:
        anim_id.animation_data.action_slot = slot


class RiftFrameAction(bpy.types.PropertyGroup):
    action: bpy.props.PointerProperty(type=bpy.types.Action)


class RiftActor(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)


class RiftFrameList(ZenuUIList[RiftFrameAction]):
    name = 'rift_frame_manager'
    _property_group = RiftFrameAction

    def _draw(self, layout: bpy.types.UILayout, item: RiftFrameAction):
        if item.action is None:
            layout.label(text='Empty')
        else:
            layout.prop(item.action, 'name', text='', emboss=False)

    def apply_action(self, action: bpy.types.Action):
        for obj in get_key_targets():
            assign_action(obj, action, obj.name, 'OBJECT')

            if obj.type == 'ARMATURE':
                assign_action(obj.data, action, obj.data.name, 'ARMATURE')

                for linked in get_objects_by_armature(obj):
                    if linked.data.shape_keys is None:
                        continue
                    assign_action(linked.data.shape_keys, action, linked.name, 'KEY')

    def _on_select(self):
        item = self.active
        if item is None or item.action is None:
            return

        self.apply_action(item.action)

    def add(self):
        return self.create_action()

    def create_action(self):
        if not get_actor_objects():
            return None

        scene = bpy.context.scene
        scene.frame_set(scene.frame_start)

        action = bpy.data.actions.new(name='Action')

        for obj in get_key_targets():
            if obj.animation_data is None:
                obj.animation_data_create()

            slot = action.slots.new('OBJECT', obj.name)
            obj.animation_data.action = action
            obj.animation_data.action_slot = slot

            if obj.type == 'ARMATURE':
                data = obj.data
                if data.animation_data is None:
                    data.animation_data_create()

                data_slot = action.slots.new('ARMATURE', data.name)
                data.animation_data.action = action
                data.animation_data.action_slot = data_slot

                for linked in get_objects_by_armature(obj):
                    key = linked.data.shape_keys
                    if key is None:
                        continue

                    if key.animation_data is None:
                        key.animation_data_create()

                    key_slot = action.slots.new('KEY', linked.name)
                    key.animation_data.action = action
                    key.animation_data.action_slot = key_slot

            insert_key(obj)

        item = super().add()
        item.action = action
        return item


class RiftActorList(ZenuUIList[RiftActor]):
    name = 'rift_actors'
    _property_group = RiftActor

    def _draw(self, layout: bpy.types.UILayout, item: RiftActor):
        layout.prop(item, 'object', text='')


rift_frame_list = RiftFrameList()
rift_actor_list = RiftActorList()


class ZENU_OT_rift_frame_manager_create_action(bpy.types.Operator):
    bl_label = 'Create Action For Actors'
    bl_idname = 'zenu.rift_frame_manager_create_action'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len(rift_actor_list.prop_list) > 0

    def execute(self, context: bpy.types.Context):
        item = rift_frame_list.create_action()
        if item is None:
            self.report({'WARNING'}, 'No actors in the list')
            return {'CANCELLED'}

        return {'FINISHED'}


class ZENU_OT_rift_frame_manager_insert_key(bpy.types.Operator):
    bl_label = 'Insert Key On Actors'
    bl_idname = 'zenu.rift_frame_manager_insert_key'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len(rift_actor_list.prop_list) > 0

    def execute(self, context: bpy.types.Context):
        if not get_actor_objects():
            self.report({'WARNING'}, 'No actors in the list')
            return {'CANCELLED'}

        for obj in get_key_targets():
            insert_key(obj)

        return {'FINISHED'}


class ZENU_OT_rift_frame_manager_render(bpy.types.Operator):
    bl_label = 'Render All Frames'
    bl_idname = 'zenu.rift_frame_manager_render'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len(rift_frame_list.prop_list) > 0

    def execute(self, context: bpy.types.Context):
        items = [item for item in rift_frame_list.prop_list if item.action is not None]
        if not items:
            self.report({'WARNING'}, 'No frames to render')
            return {'CANCELLED'}

        try:
            bpy.ops.wm.console_toggle()
        except RuntimeError:
            pass

        scene = context.scene
        directory = bpy.path.abspath(scene.render.filepath)
        os.makedirs(directory, exist_ok=True)
        ext = scene.render.file_extension
        total = len(items)

        for index, item in enumerate(items):
            print(f'[Rift Frame Manager] Rendering {index + 1}/{total}: {item.action.name}', flush=True)

            rift_frame_list.apply_action(item.action)
            scene.frame_set(scene.frame_start)

            bpy.ops.render.render(write_still=False)

            result = bpy.data.images.get('Render Result')
            if result is None:
                continue

            filepath = os.path.join(directory, item.action.name + ext)
            result.save_render(filepath=filepath)
            print(f'[Rift Frame Manager] Saved: {filepath}', flush=True)

        print(f'[Rift Frame Manager] Done. Rendered {total} frame(s).', flush=True)
        return {'FINISHED'}


class ZENU_PT_rift_frame_manager(RiftBasePanel):
    bl_label = 'Frame Manager'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        rift_frame_list.draw_ui(layout=layout)

        item = rift_frame_list.active
        if item is not None:
            layout.prop(item, 'action', text='')
        
        layout.operator(ZENU_OT_rift_frame_manager_insert_key.bl_idname, icon='KEYFRAME_HLT')
        layout.operator(ZENU_OT_rift_frame_manager_render.bl_idname, icon='RENDER_STILL')


class ZENU_PT_rift_actors(RiftBasePanel):
    bl_label = 'Actors'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        rift_actor_list.draw_ui(layout=layout)
        layout.operator(ZENU_OT_rift_frame_manager_create_action.bl_idname, icon='ACTION')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_rift_frame_manager_create_action,
    ZENU_OT_rift_frame_manager_insert_key,
    ZENU_OT_rift_frame_manager_render,
    ZENU_PT_rift_frame_manager,
    ZENU_PT_rift_actors,
))


def register():
    reg()
    rift_frame_list.register()
    rift_actor_list.register()


def unregister():
    unreg()
    rift_frame_list.unregister()
    rift_actor_list.unregister()

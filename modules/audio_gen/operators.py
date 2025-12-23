import json
import os.path
import random

import bpy
from bpy_extras.io_utils import ImportHelper
from .property_groups import TriggerCalcResult, realtime_data
from .utils import calc_triggers, get_active_point, get_active_point_index, get_active_trigger, \
    get_active_trigger_index, \
    add_sound
from ...utils import get_collection


class ZENU_OT_trigger_action(bpy.types.Operator):
    bl_label = 'Trigger Action'
    bl_idname = 'zenu.trigger_action'
    bl_options = {'UNDO'}
    type: bpy.props.EnumProperty(items=(
        ('POINT', 'Point', ''),
        ('TRIGGER', 'Trigger', '')
    ))
    action: bpy.props.EnumProperty(items=(
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
        ('CLEAR', 'Clear', ''),
    ))

    def execute(self, context: bpy.types.Context):
        if self.type == 'POINT':
            data = context.scene.zenu_at_point
            tri_obj = get_active_point()
            index = get_active_point_index()
            action_display = 'PLAIN_AXES'
            name = 'TriggerPoint'
        else:
            data = context.scene.zenu_at
            tri_obj = get_active_trigger()
            index = get_active_trigger_index()
            action_display = 'SPHERE'
            name = 'Trigger'

        if self.action == 'ADD':
            coll = get_collection('AudioGen')
            obj = bpy.data.objects.new(name, None)
            coll.objects.link(obj)

            trigger = data.add()
            trigger.obj = obj
            obj.empty_display_type = action_display
        elif self.action == 'REMOVE':
            bpy.data.objects.remove(tri_obj.obj, do_unlink=True)
            data.remove(index)
        elif self.action == 'CLEAR':
            data.clear()

        return {'FINISHED'}


class ZENU_OT_calculate_triggers(bpy.types.Operator):
    bl_label = 'Calculate Tringgers'
    bl_idname = 'zenu.calculate_triggers'

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        triggered = {}
        data = {}
        s = scene.sequence_editor.sequences

        for key, item in s.items():
            if item.channel == 3:
                s.remove(item)

        for i in range(scene.frame_start, scene.frame_end + 1):
            triggers = calc_triggers()
            index = i - 1

            for trigger in triggers:
                t = triggered.get(trigger.name)

                if t is not None and t != trigger.is_triggered:
                    add_sound(t, trigger, index)
                    data[index] = t

                triggered[trigger.name] = trigger.is_triggered

            scene.frame_set(i)

        return {'FINISHED'}


class ZENU_OT_calculate_triggers_realtime(bpy.types.Operator):
    bl_label = 'Realtime calc'
    bl_idname = 'zenu.calculate_triggers_realtime'
    bl_options = {'UNDO'}

    @staticmethod
    def add_audio(triggers: list[TriggerCalcResult]):
        scene = bpy.context.scene
        frame = scene.frame_current
        for trigger in triggers:
            t = realtime_data.triggered.get(trigger.name)

            if t is not None and t != trigger.is_triggered:
                add_sound(t, trigger, frame)

            realtime_data.triggered[trigger.name] = trigger.is_triggered

    def execute(self, context: bpy.types.Context):
        strips = context.scene.sequence_editor.strips

        for strip in strips:
            if strip.channel == 3:
                strips.remove(strip)

        realtime_data.is_record = True
        realtime_data.on_frame_update = self.add_audio

        context.scene.frame_set(context.scene.frame_start)
        bpy.ops.screen.animation_play()
        return {'FINISHED'}


class ZENU_OT_calculate_triggers_realtime_clipboard(bpy.types.Operator):
    bl_label = 'Realtime calc clipboard'
    bl_idname = 'zenu.calculate_triggers_realtime_clipboard'
    bl_options = {'UNDO'}
    data_global = {
        'triggers': []
    }

    @classmethod
    def add_audio(cls, triggers: list[TriggerCalcResult]):

        scene = bpy.context.scene
        frame = scene.frame_current
        for trigger in triggers:
            t = realtime_data.triggered.get(trigger.name)

            if t is not None and t != trigger.is_triggered:
                if not t:
                    cls.data_global['triggers'].append((
                        frame
                    ))

            realtime_data.triggered[trigger.name] = trigger.is_triggered

    @classmethod
    def on_end(cls):
        bpy.context.window_manager.clipboard = json.dumps(cls.data_global)

    def execute(self, context: bpy.types.Context):
        self.data_global['triggers'].clear()
        realtime_data.is_record = True
        realtime_data.on_frame_update = self.add_audio
        realtime_data.on_end = self.on_end

        context.scene.frame_set(context.scene.frame_start)
        bpy.ops.screen.animation_play()
        return {'FINISHED'}


class ZENU_random_audio_import(bpy.types.Operator, ImportHelper):
    bl_idname = "zenu.random_audio_import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Random Audio Import"

    # ImportHelper mixin class uses this
    filename_ext = ".txt"

    filter_glob: bpy.props.StringProperty(
        default="*.mp3;*.wav;*.flac",
        options={'HIDDEN'},
    )

    filename: bpy.props.StringProperty(maxlen=1024)
    directory: bpy.props.StringProperty(maxlen=1024)

    files: bpy.props.CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)

    def execute(self, context):
        # print()
        files: list[str] = [os.path.join(self.directory, file.name) for file in self.files]

        for seq in context.scene.sequence_editor.strips_all:
            if seq.type != 'SOUND':
                continue
            
            if not seq.select:
                continue
            
            seq: bpy.types.SoundStrip

            file = random.choice(files)
            sound = bpy.data.sounds.load(file, check_existing=True)

            # print(seq, sound)
            seq.sound = sound

        return {'FINISHED'}


classes = (
    ZENU_OT_trigger_action,
    ZENU_OT_calculate_triggers,
    ZENU_OT_calculate_triggers_realtime,
    ZENU_OT_calculate_triggers_realtime_clipboard,
    ZENU_random_audio_import
)

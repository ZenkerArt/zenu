import json
import os
import random
from collections import defaultdict

import bpy as bpy
from bpy_extras.io_utils import ImportHelper

from .property_groups import TriggerCalcResult, realtime_data, TriggerCache
from .utils import add_video
import bpy


def active_cache() -> TriggerCache:
    return bpy.context.scene.zenu_trigger_cache[bpy.context.scene.zenu_trigger_cache_active]


class ZENU_OT_calculate_triggers_realtime_cache(bpy.types.Operator):
    bl_label = 'Realtime Calc Cache'
    bl_idname = 'zenu.calculate_triggers_realtime_cache'
    bl_options = {'UNDO'}
    data_global = {
        'triggers': defaultdict(list)
    }

    def cache(self, triggers: list[TriggerCalcResult]):
        scene = bpy.context.scene
        frame = scene.frame_current
        for trigger in triggers:
            t = realtime_data.triggered.get(trigger.name)
            if trigger.is_triggered:
                print(trigger.name, trigger.is_triggered)

            if t is not None and t != trigger.is_triggered:
                if not t:
                    self.data_global['triggers'][frame].append(trigger.name)

            realtime_data.triggered[trigger.name] = trigger.is_triggered

    def on_end(self):
        item = bpy.context.scene.zenu_trigger_cache.add()
        item.data = json.dumps(self.data_global)
        item.name = 'Cache'

    def execute(self, context: bpy.types.Context):
        self.data_global['triggers'].clear()
        realtime_data.is_record = True
        realtime_data.on_frame_update = self.cache
        realtime_data.on_end = self.on_end

        context.scene.frame_set(context.scene.frame_start)
        bpy.ops.screen.animation_play()
        return {'FINISHED'}


class ZENU_OT_pasts_videos_from_clipboard(bpy.types.Operator):
    bl_label = 'Past Videos From Cache'
    bl_idname = 'zenu.pasts_videos_from_clipboard'

    # filename_ext = ".txt"

    def execute(self, context: bpy.types.Context):
        data = json.loads(active_cache().data)['triggers']

        for key, names in data.items():
            if 'splash' in names:
                add_video(int(key), r'C:\Users\zenke\Desktop\BlenderProjects\Addons\Zenu\Bounces',
                          'Video').blend_type = 'ADD'
        return {'FINISHED'}


class ZENU_OT_pasts_audio_from_clipboard(bpy.types.Operator, ImportHelper):
    bl_label = 'Past Audio From Cache'
    bl_idname = 'zenu.pasts_audio_from_clipboard'
    filter_glob: bpy.props.StringProperty(
        default="*.mp3;*.wav;*.flac",
        options={'HIDDEN'},
    )

    filename: bpy.props.StringProperty(maxlen=1024)
    directory: bpy.props.StringProperty(maxlen=1024)

    files: bpy.props.CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)

    def execute(self, context: bpy.types.Context):
        data = json.loads(active_cache().data)['triggers']

        files: list[str] = [os.path.join(self.directory, file.name) for file in self.files]
        s = context.scene.sequence_editor.sequences

        for key, names in data.items():
            frame = int(key)

            file = random.choice(files)
            s.new_sound('audio', file, 3, frame - 1)
        return {'FINISHED'}


classes = (
    ZENU_OT_calculate_triggers_realtime_cache,
    ZENU_OT_pasts_videos_from_clipboard,
    ZENU_OT_pasts_audio_from_clipboard
)

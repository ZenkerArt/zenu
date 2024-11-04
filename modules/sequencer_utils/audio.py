import datetime
import os
import time
import re
from dataclasses import dataclass

import unicodedata

import bpy
from ...base_panel import BasePanel


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


class ZENU_OT_export_selected_strips(bpy.types.Operator):
    bl_label = 'Export Selected Strips'
    bl_idname = 'zenu.export_selected_strips'

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}


def string_to_time(value: str):
    x = time.strptime(value.split(',')[0], '%H:%M:%S')

    return datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()


@dataclass
class SrtBlock:
    number: int
    time_start: float
    time_end: float
    body: str

    @property
    def frame_start(self):
        return int(self.time_start * bpy.context.scene.render.fps)

    @property
    def frame_end(self):
        return int(self.time_end * bpy.context.scene.render.fps)


def parse_srt(srt_path: str):
    srt_path: str = bpy.path.abspath(srt_path)
    r_unwanted = re.compile("[\n\t\r]")
    result = []

    with open(srt_path, mode='r') as f:
        blocks = f.read().split('\n\n')

    for block in blocks:
        try:
            subtitle_number, timing, body = block.split('\n', maxsplit=2)
        except ValueError as e:
            print(e)
            continue
        subtitle_number = int(subtitle_number)
        time_start, time_end = tuple(string_to_time(i.strip()) for i in timing.split('-->'))
        body = r_unwanted.sub('', body)

        result.append(SrtBlock(
            number=subtitle_number,
            time_start=time_start,
            time_end=time_end,
            body=body
        ))

    return result


class ZENU_OT_add_srt_markers(bpy.types.Operator):
    bl_label = 'Add Srt Markers'
    bl_idname = 'zenu.add_srt_markers'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        srt_path: str = context.scene.zenu_srt_path
        for block in parse_srt(srt_path):
            context.scene.timeline_markers.new(f'{block.number}) {block.body}', frame=block.frame_start)
            context.scene.timeline_markers.new(f'{block.number}) End', frame=block.frame_end)

        return {'FINISHED'}


class ZENU_OT_cut_strip_by_srt(bpy.types.Operator):
    bl_label = 'Cut Strip By Srt'
    bl_idname = 'zenu.cut_strip_by_srt'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        srt_path: str = context.scene.zenu_srt_path
        strip = context.active_sequence_strip
        sound: bpy.types.Sound = strip.sound
        print(sound.filepath)

        for block in parse_srt(srt_path):
            strip1 = context.scene.sequence_editor.sequences.new_sound(name='Test', frame_start=block.frame_start,
                                                                       channel=0,
                                                                       filepath='')
            strip1.sound = sound
            strip1.frame_offset_start = block.frame_start
            strip1.frame_final_start = block.frame_start
            strip1.frame_final_end = block.frame_end
            strip1.name = block.body

            # context.scene.timeline_markers.new(f'{block.number}) {block.body}', frame=block.frame_start)
            # context.scene.timeline_markers.new(f'{block.number}) End', frame=block.frame_end)

        return {'FINISHED'}


class ZENU_OT_export_selected_strips(bpy.types.Operator):
    bl_label = 'Export Selected Strips'
    bl_idname = 'zenu.export_selected_strips'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        audio_path = bpy.path.abspath(context.scene.zenu_audio_export)
        # if not os.path.exists(audio_path):
        #     os.mkdir(audio_path)

        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end

        for strip in context.selected_sequences:
            strip: bpy.types.Sequence

            context.scene.frame_start = int(strip.frame_final_start)
            context.scene.frame_end = int(strip.frame_final_end)

            name = slugify(strip.name)

            bpy.ops.sound.mixdown(filepath=os.path.join(audio_path, f'{name}.wav'), codec='AAC')

        context.scene.frame_start = frame_start
        context.scene.frame_end = frame_end

        return {'FINISHED'}


class ZENU_PT_Utils(BasePanel):
    bl_label = 'Utils'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        layout.label(text='Srt Import')
        col = layout.column(align=True)
        col.prop(context.scene, 'zenu_srt_path')
        col.operator(ZENU_OT_add_srt_markers.bl_idname)
        col.prop(context.scene, 'zenu_audio_export')
        col.operator(ZENU_OT_export_selected_strips.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_export_selected_strips,
    ZENU_OT_add_srt_markers,
    ZENU_OT_cut_strip_by_srt,
    ZENU_PT_Utils
))


def register():
    bpy.types.Scene.zenu_srt_path = bpy.props.StringProperty(name='Srt Path', subtype='FILE_PATH')
    bpy.types.Scene.zenu_audio_export = bpy.props.StringProperty(name='Audio Export Path', subtype='DIR_PATH',
                                                                 default='//')
    reg()


def unregister():
    unreg()

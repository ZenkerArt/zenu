import os
import random

import bpy
from .property_groups import AudioTrigger, TriggerCalcResult, AudioTriggerPoint


def add_sound(state: bool, trigger: TriggerCalcResult, frame: int):
    if state:
        return

    scene = bpy.context.scene

    folder = bpy.path.abspath(trigger.trigger.path)
    files = []
    for file in os.scandir(folder):
        files.append(file.path)
    s = scene.sequence_editor.sequences
    s.new_sound(trigger.name, random.choice(files), 3, frame - 1)


def add_video(frame: int, folder: str, name: str) -> bpy.types.MovieSequence:
    scene = bpy.context.scene

    folder = bpy.path.abspath(folder)
    files = []
    for file in os.scandir(folder):
        files.append(file.path)
    s = scene.sequence_editor.sequences
    movie = s.new_movie(name, random.choice(files), 4, frame - 1)
    print(f'add video {frame}')
    return movie


def calc_triggers():
    scene = bpy.context.scene
    triggered_list = []

    for trigger in scene.zenu_at:
        trigger: AudioTrigger
        trigger_obj: bpy.types.Object = trigger.obj
        radius = sum(trigger_obj.scale) / 3

        is_triggered = False

        triggered = TriggerCalcResult(
            trigger=trigger,
            radius=radius,
            is_triggered=is_triggered
        )

        for point in scene.zenu_at_point:
            pos1 = point.obj.matrix_world.translation
            pos2 = trigger_obj.matrix_world.translation

            diff = pos1 - pos2

            is_triggered = abs(diff.length) < radius
            triggered.points.append(point)

            if is_triggered:
                break

        triggered.is_triggered = is_triggered
        triggered_list.append(triggered)

    return triggered_list


def get_active_trigger_index():
    return bpy.context.scene.zenu_at_active


def get_active_trigger() -> AudioTrigger | None:
    try:
        return bpy.context.scene.zenu_at[get_active_trigger_index()]
    except IndexError:
        return None


def get_active_point_index():
    return bpy.context.scene.zenu_at_point_active


def get_active_point() -> AudioTriggerPoint | None:
    try:
        return bpy.context.scene.zenu_at_point[get_active_point_index()]
    except IndexError:
        return None

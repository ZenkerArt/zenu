import os
import random
from dataclasses import field, dataclass

import bpy
from bpy.app.handlers import persistent
from .property_groups import AudioTrigger, AudioTriggerPoint
from ...base_panel import BasePanel
from ...utils import get_collection


@dataclass()
class RealtimeData:
    is_record: bool = False
    triggered: dict[str, bool] = field(default_factory=dict)


realtime_data = RealtimeData()


def add_sound(state: bool, trigger: 'TriggerCalcResult', frame: int):
    if state:
        return

    scene = bpy.context.scene

    folder = bpy.path.abspath(trigger.trigger.path)
    files = []
    for file in os.scandir(folder):
        files.append(file.path)
    s = scene.sequence_editor.sequences
    s.new_sound(trigger.name, random.choice(files), 3, frame - 1)


@persistent
def update(scene: bpy.types.Scene):
    if not realtime_data.is_record:
        return
    triggers = calc_triggers()

    frame = scene.frame_current
    for trigger in triggers:
        t = realtime_data.triggered.get(trigger.name)

        if t is not None and t != trigger.is_triggered:
            add_sound(t, trigger, frame)

        realtime_data.triggered[trigger.name] = trigger.is_triggered

    if frame >= scene.frame_end - 2:
        realtime_data.is_record = False
        bpy.ops.screen.animation_cancel()


@dataclass
class TriggerCalcResult:
    trigger: 'AudioTrigger'
    radius: float
    is_triggered: bool
    points: list['AudioTriggerPoint'] = field(default_factory=list)

    @property
    def name(self):
        return self.trigger.name


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

        triggered.is_triggered = is_triggered
        triggered_list.append(triggered)

    return triggered_list


def get_active_index():
    return bpy.context.scene.zenu_at_active


def get_active_trigger() -> AudioTrigger | None:
    try:
        return bpy.context.scene.zenu_at[get_active_point_index()]
    except IndexError:
        return None


def get_active_point_index():
    return bpy.context.scene.zenu_at_point_active


def get_active_point() -> AudioTriggerPoint | None:
    try:
        return bpy.context.scene.zenu_at_point[get_active_point_index()]
    except IndexError:
        return None


class ZENU_UL_triggers_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item
        layout.prop(slot, 'name', text='', emboss=False)


class ZENU_OT_trigger_action(bpy.types.Operator):
    bl_label = 'Trigger Action'
    bl_idname = 'zenu.trigger_action'
    bl_options = {'UNDO'}
    type: bpy.props.EnumProperty(items=(
        ('POINT', 'Add', ''),
        ('TRIGGER', 'Remove', '')
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
            index = get_active_index()
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


class ZENU_PT_audio_gen(BasePanel):
    bl_label = 'Audio Gen'

    def audio_triggers(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column(align=True)
        col.template_list('ZENU_UL_triggers_list', '', context.scene, 'zenu_at', context.scene,
                          'zenu_at_active')

        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Add')
        op.action = 'ADD'
        op.type = 'TRIGGER'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Remove')
        op.action = 'REMOVE'
        op.type = 'TRIGGER'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Clear')
        op.action = 'CLEAR'
        op.type = 'TRIGGER'

        col = layout.column(align=True)
        item = get_active_trigger()

        if item is None:
            return

        col.prop(item, 'obj')
        col.prop(item, 'path')

    def audio_triggers_point(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column(align=True)
        col.template_list('ZENU_UL_triggers_list', '', context.scene, 'zenu_at_point', context.scene,
                          'zenu_at_point_active')
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Add')
        op.action = 'ADD'
        op.type = 'POINT'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Remove')
        op.action = 'REMOVE'
        op.type = 'POINT'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Clear')
        op.action = 'CLEAR'
        op.type = 'POINT'

        col = layout.column(align=True)
        item = get_active_point()

        if item is None:
            return

        col.prop(item, 'obj')

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        self.audio_triggers(context)

        layout.label(text='Trigger Pointsт')
        self.audio_triggers_point(context)

        layout.operator(ZENU_OT_calculate_triggers.bl_idname)
        layout.operator(ZENU_OT_realtime_audio_gen.bl_idname)


class ZENU_OT_realtime_audio_gen(bpy.types.Operator):
    bl_label = 'Realtime calc'
    bl_idname = 'zenu.realtime_audio_gen'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        s: dict[str, bpy.types.Sequence] = context.scene.sequence_editor.sequences

        for key, item in s.items():
            if item.channel == 3:
                s.remove(item)

        realtime_data.is_record = True
        context.scene.frame_set(context.scene.frame_start)
        bpy.ops.screen.animation_play()
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_trigger_action,
    ZENU_OT_calculate_triggers,
    ZENU_OT_realtime_audio_gen,
    ZENU_UL_triggers_list,
    ZENU_PT_audio_gen,
    AudioTriggerPoint,
    AudioTrigger
))


def select_trigger(scene: bpy.types.Scene, context: bpy.types.Context):
    trigger = get_active_trigger()
    bpy.ops.object.select_all(action='DESELECT')
    obj: bpy.types.Object = trigger.obj
    obj.select_set(True)

    context.view_layer.objects.active = obj


def select_point(scene: bpy.types.Scene, context: bpy.types.Context):
    trigger = get_active_point()
    bpy.ops.object.select_all(action='DESELECT')
    obj: bpy.types.Object = trigger.obj
    obj.select_set(True)

    context.view_layer.objects.active = obj


def register():
    bpy.app.handlers.frame_change_post.append(update)
    reg()

    bpy.types.Scene.zenu_at = bpy.props.CollectionProperty(type=AudioTrigger)
    bpy.types.Scene.zenu_at_active = bpy.props.IntProperty(update=select_trigger)

    bpy.types.Scene.zenu_at_point = bpy.props.CollectionProperty(type=AudioTriggerPoint)
    bpy.types.Scene.zenu_at_point_active = bpy.props.IntProperty(update=select_point)


def unregister():
    bpy.app.handlers.frame_change_post.remove(update)
    unreg()

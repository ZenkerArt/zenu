import bpy
from bpy.app.handlers import persistent
from .property_groups import AudioTrigger, AudioTriggerPoint, realtime_data, TriggerCache
from .ui import ZENU_PT_audio_gen
from .utils import calc_triggers, get_active_trigger, get_active_point
from . import operators, ui, cache_operators


@persistent
def update(scene: bpy.types.Scene):
    if not realtime_data.is_record:
        return
    triggers = calc_triggers()
    frame = scene.frame_current

    realtime_data.on_frame_update(triggers)

    if frame >= scene.frame_end - 2:
        realtime_data.is_record = False
        bpy.ops.screen.animation_cancel()
        realtime_data.on_end()


reg, unreg = bpy.utils.register_classes_factory((
    *cache_operators.classes,
    *operators.classes,
    *ui.classes,
    AudioTriggerPoint,
    AudioTrigger,
    TriggerCache
))


def select_trigger(scene: bpy.types.Scene, context: bpy.types.Context):
    trigger = get_active_trigger()
    print(trigger.name, trigger.name)

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

    bpy.types.Scene.zenu_trigger_cache = bpy.props.CollectionProperty(type=TriggerCache)
    bpy.types.Scene.zenu_trigger_cache_active = bpy.props.IntProperty()

    bpy.types.Scene.zenu_at = bpy.props.CollectionProperty(type=AudioTrigger)
    bpy.types.Scene.zenu_at_active = bpy.props.IntProperty(update=select_trigger)

    bpy.types.Scene.zenu_at_point = bpy.props.CollectionProperty(type=AudioTriggerPoint)
    bpy.types.Scene.zenu_at_point_active = bpy.props.IntProperty(update=select_point)


def unregister():
    bpy.app.handlers.frame_change_post.remove(update)
    unreg()

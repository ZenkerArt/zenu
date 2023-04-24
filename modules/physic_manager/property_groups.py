import bpy
from .utils import get_cloth


def apply_object_cloth_settings(obj: bpy.types.Object):
    scene_settings: PhysicSettingScene = bpy.context.scene.physic_setting
    cloth = get_cloth(obj)
    if cloth is None:
        return
    object_settings = obj.physic_setting
    if object_settings.ignore:
        return

    cloth.point_cache.frame_start = scene_settings.start + object_settings.start
    cloth.point_cache.frame_end = scene_settings.end + object_settings.end


def object_settings_update(self: 'PhysicSetting', context: bpy.types.Context):
    apply_object_cloth_settings(context.active_object)


def scene_settings_update(self: 'PhysicSetting', context: bpy.types.Context):
    aplay_scene_cloth_settings()


def aplay_scene_cloth_settings():
    for i in bpy.context.scene.objects:
        apply_object_cloth_settings(i)


class PhysicSetting(bpy.types.PropertyGroup):
    start: bpy.props.IntProperty(name='Start Offset', update=object_settings_update)
    end: bpy.props.IntProperty(name='End Offset', update=object_settings_update)
    ignore: bpy.props.BoolProperty(name='Ignore')
    group: bpy.props.StringProperty(name='Group')


class PhysicSettingScene(bpy.types.PropertyGroup):
    start: bpy.props.IntProperty(name='Start', update=scene_settings_update)
    end: bpy.props.IntProperty(name='End', update=scene_settings_update)


def PhysicGroup_on_enable_update(self, context: bpy.types.Context):
    for i in context.scene.objects:
        cloth = get_cloth(i)
        if cloth is None or i.physic_group != str(self.id):
            continue

        cloth.show_viewport = self.enable
        cloth.show_render = self.enable
        i.hide_viewport = self.view


class PhysicGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    id: bpy.props.IntProperty()
    enable: bpy.props.BoolProperty(default=True, update=PhysicGroup_on_enable_update)
    view: bpy.props.BoolProperty(default=False, update=PhysicGroup_on_enable_update)


classes = (
    PhysicSetting,
    PhysicSettingScene,
    PhysicGroup
)

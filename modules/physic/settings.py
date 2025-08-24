import bpy


class ZPhysicSettingsType:
    auto_sort: bool = True


class ZPhysicSettings(bpy.types.PropertyGroup):
    auto_sort: bpy.props.BoolProperty(name='Auto Sort', default=True)


class ZPhysicSettingsBone(bpy.types.PropertyGroup):
    order: bpy.props.IntProperty()


def get_physic_settings() -> ZPhysicSettingsType:
    return bpy.context.scene.zenu_physic_settings

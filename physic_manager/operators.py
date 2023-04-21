import json
from typing import Any, Type

import bpy
from mathutils import Vector
from .utils import get_cloth
from .physic_presets import physic_presets, PhysicPreset, get_current_preset
from ..utils import update_window


def bpy_struct_to_dict(struct: bpy.types.bpy_struct,
                       ignore: list[str] = None,
                       recursion_max: int = 2,
                       recursion_counter: int = 0) -> dict[str, Any]:
    if recursion_counter > recursion_max:
        return {}

    struct_type = struct.bl_rna
    ignore = ignore or []
    dct = {}

    for key in struct_type.properties.keys():
        if any([key.startswith(i) for i in ignore]) or key.startswith('rna'):
            continue
        data = getattr(struct, key, None)

        if isinstance(data, bpy.types.bpy_struct):
            data = bpy_struct_to_dict(data,
                                      ignore=ignore,
                                      recursion_max=recursion_max,
                                      recursion_counter=recursion_counter + 1)
            if not data:
                continue
        if isinstance(data, Vector):
            data = data.to_tuple()

        dct[key] = data

    return dct


def cloth_settings_to_dict(obj: bpy.types.Object):
    cloth = get_cloth(obj)
    dct = bpy_struct_to_dict(cloth.settings, ignore=[
        'rest_shape_key',
        'collection',
        'vertex_group'
    ])
    return dct


class ZENU_OT_physic_save(bpy.types.Operator):
    bl_label = 'Physic Save'
    bl_idname = 'zenu.physic_to_json'

    obj: bpy.props.StringProperty(name='Object Name')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_cloth(context.active_object) and get_current_preset()

    def draw(self, context: 'Context'):
        self.layout.label(text='Override preset?')

    def execute(self, context: bpy.types.Context):
        obj = bpy.data.objects.get(self.obj) or context.active_object
        preset = get_current_preset()
        dct = cloth_settings_to_dict(obj)
        preset.save(dct)

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return bpy.context.window_manager.invoke_props_dialog(self)

class ZENU_OT_physic_load(bpy.types.Operator):
    bl_label = 'Physic Load'
    bl_idname = 'zenu.json_to_physic'

    obj: bpy.props.StringProperty(name='Object Name')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_cloth(context.active_object) and get_current_preset()

    def dict_to_bpy_struct(self, struct: bpy.types.bpy_struct, dct: dict[str, Any]) -> dict[str, Any]:

        for key, value in dct.items():
            if isinstance(value, list):
                value = Vector(tuple(value))

            if isinstance(value, dict):
                self.dict_to_bpy_struct(getattr(struct, key), value)
                continue

            setattr(struct, key, value)

    def execute(self, context: bpy.types.Context):
        obj = bpy.data.objects.get(self.obj) or context.active_object
        cloth = get_cloth(obj)
        preset = get_current_preset()
        self.dict_to_bpy_struct(cloth.settings, preset.load())
        return {'FINISHED'}


class ZENU_OT_physic_create_preset(bpy.types.Operator):
    bl_label = 'Create Preset'
    bl_description = 'Create Preset'
    bl_idname = 'zenu.physic_create_preset'

    name: bpy.props.StringProperty(name='Preset Name')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_cloth(context.active_object)

    def execute(self, context: bpy.types.Context):
        name = self.name.strip()
        if not name or name in [i.name for i in physic_presets]:
            return {'CANCELLED'}

        preset = PhysicPreset(name=name)
        physic_presets.append(preset)
        dct = cloth_settings_to_dict(context.active_object)
        preset.save(dct)

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return bpy.context.window_manager.invoke_props_dialog(self)


class ZENU_OT_physic_remove_preset(bpy.types.Operator):
    bl_label = 'Remove Preset'
    bl_description = 'Remove Preset'
    bl_idname = 'zenu.physic_remove_preset'

    @classmethod
    def poll(cls, context: 'Context'):
        return get_current_preset()

    def execute(self, context: bpy.types.Context):
        data = get_current_preset()
        data.remove()
        physic_presets.remove(data)
        try:
            if not context.scene.physic_presets:
                context.scene.physic_presets = physic_presets[-1].name.upper()
        except IndexError:
            pass
        update_window()
        return {'FINISHED'}


class ZENU_OT_physic_select_all(bpy.types.Operator):
    bl_label = 'Select All'
    bl_idname = 'zenu.physic_select_all'

    def execute(self, context: 'Context'):
        for i in context.scene.objects:
            if get_cloth(i) is None:
                continue

            i.select_set(True)
        return {'FINISHED'}


class ZENU_OT_physic_bake_object(bpy.types.Operator):
    bl_label = 'Bake Simulation'
    bl_idname = 'zenu.physic_bake_object'
    end: bpy.props.BoolProperty()
    type: bpy.props.EnumProperty(items={
        ('bake', 'Bake', ''),
        ('free', 'Free', ''),
        ('frame', 'Frame', ''),
    })

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_cloth(context.active_object) is not None

    def execute(self, context: bpy.types.Context):
        cloth = get_cloth(context.active_object)
        cache = cloth.point_cache

        override = {'blend_data': bpy.data, 'scene': context.scene, 'active_object': context.object,
                    'point_cache': cache}
        if self.type == 'bake':
            bpy.ops.ptcache.bake(override, 'INVOKE_DEFAULT', bake=True)
        elif self.type == 'free':
            bpy.ops.ptcache.free_bake(override, 'INVOKE_DEFAULT')
        elif self.type == 'frame':
            bpy.ops.ptcache.bake(override, 'INVOKE_DEFAULT', bake=False)
        return {'FINISHED'}


class ZENU_OT_physic_rest_time_scene(bpy.types.Operator):
    bl_label = 'Rest Time'
    bl_idname = 'zenu.physic_rest_end_time_scene'
    end: bpy.props.BoolProperty()

    def execute(self, context: bpy.types.Context):
        if self.end:
            context.scene.physic_setting.end = context.scene.frame_end
        else:
            context.scene.physic_setting.start = context.scene.frame_start
        return {'FINISHED'}


class ZENU_OT_physic_rest_time_object(bpy.types.Operator):
    bl_label = 'Rest Time'
    bl_idname = 'zenu.physic_rest_end_time_object'
    end: bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_cloth(context.active_object) is not None

    def execute(self, context: bpy.types.Context):
        if self.end:
            context.active_object.physic_setting.end = 0
        else:
            context.active_object.physic_setting.start = 0
        return {'FINISHED'}


classes = (
    ZENU_OT_physic_select_all,
    ZENU_OT_physic_bake_object,
    ZENU_OT_physic_rest_time_scene,
    ZENU_OT_physic_rest_time_object,
    ZENU_OT_physic_save,
    ZENU_OT_physic_load,
    ZENU_OT_physic_create_preset,
    ZENU_OT_physic_remove_preset
)

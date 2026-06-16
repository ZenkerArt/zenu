import json

import bpy

from .face_conf import face_conf
from .preset import Preset, ShapeProperty
from ..rift.generators.eye_target import EYE_TARGET_NAME
from ...base_panel import RiftBasePanel


def default(var: float):
    return var


def invert(var: float):
    return 1 - var


functions = {
    'invert': invert,
    'default': default
}


def get_preset(category: str):
    def func(self, context):
        lst = []

        for shape in face_conf.all():
            if shape.category.lower() == category:
                lst.append((
                    shape.name,
                    shape.name,
                    ''
                ))

        return lst

    return func


def get_objects_by_armature(armature: bpy.types.Object) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for obj_mod in bpy.data.objects.values():
        obj_mod: bpy.types.Object
        if not isinstance(obj_mod.data, bpy.types.Mesh): continue

        if obj_mod.data.shape_keys is None:
            continue

        for mod in obj_mod.modifiers.values():
            mod: bpy.types.ArmatureModifier
            if isinstance(mod, bpy.types.ArmatureModifier) and mod.object == armature:
                objects.append(obj_mod)

    return objects


def on_character_preset_change(category: str):
    def func(self, context):
        objects: list[bpy.types.Object] = get_objects_by_armature(self.armature_object)

        preset = getattr(self, f'{category}_preset')
        open = getattr(self, f'{category}_open')

        shape = face_conf.get_by_name(preset)
        # for obj in objects:
        #     for s in obj.data.shape_keys.key_blocks:
        #         s.value = 0

        shape_keys = shape.get_object_shapes(objects)

        for shape_key, prop in shape_keys:
            shape_key.value = functions[prop.function](open)

    return func


def preset_setter(category: str):
    def func(self, value):
        prev_value = self.id_data.get(f'{category}_preset') or 0

        objects: list[bpy.types.Object] = get_objects_by_armature(self.armature_object)

        for shape_prop in face_conf.get_by_category(category):
            # shape_prop = face_conf.get_by_enum_index(category, prev_value)
            shape_keys = shape_prop.get_object_shapes(objects)

            for shape_key, prop in shape_keys:
                shape_key.value = 0

        self.id_data[f'{category}_preset'] = value

    return func


def preset_getter(category: str):
    def func(self: 'CharacterControl'):
        return self.id_data.get(f'{category}_preset') or 0

    return func


class CharacterControl(bpy.types.PropertyGroup):
    eye_preset: bpy.props.EnumProperty(items=face_conf.get_dynamic_enum('eye'),
                                         update=on_character_preset_change('eye'),
                                         get=preset_getter('eye'),
                                         set=preset_setter('eye'), name='Eye Presets')

    mouth_preset: bpy.props.EnumProperty(items=face_conf.get_dynamic_enum('mouth'),
                                         update=on_character_preset_change('mouth'),
                                         get=preset_getter('mouth'),
                                         set=preset_setter('mouth'), name='Mouth Presets')

    eye_open: bpy.props.FloatProperty(subtype='FACTOR', min=0, max=1, update=on_character_preset_change('eye'))
    mouth_open: bpy.props.FloatProperty(subtype='FACTOR', min=0, max=1, update=on_character_preset_change('mouth'))

    armature_object: bpy.props.PointerProperty(type=bpy.types.Object)


class ZENU_OT_generate_presets(bpy.types.Operator):
    bl_label = 'Generate Presets'
    bl_idname = 'zenu.generate_presets'

    def execute(self, context: bpy.types.Context):
        obj = context.active_object

        shapes: list[str] = []
        presets: dict[str, set[str]] = {}
        presets_final: list[Preset] = []

        for shape in obj.data.shape_keys.key_blocks:
            d = shape.name.split('_', maxsplit=1)[0].replace('k', '').replace('e', '')
            if not d.isdigit(): continue

            prefix = 'Eye' if shape.name.startswith('e') else 'Mouth'
            data = presets.get(f'{prefix}_{d}') or set()
            data.add(shape.name)
            presets[f'{prefix}_{d}'] = data

        for preset_name, data in presets.items():
            cat, num = preset_name.split('_')
            p = Preset(
                name=f'{cat} - {num}',
                category=cat
            )

            for prest in data:
                p.properties.append(ShapeProperty(
                    shape=prest,
                    function='default' if prest.endswith('op') else 'invert'
                ))

            presets_final.append(p)

        bpy.context.window_manager.clipboard = json.dumps([i.to_dict() for i in presets_final], indent=2)
        # for p in [i.to_dict() for i in presets_final]:
        #     print(Preset.from_dict(p))
        return {'FINISHED'}


class ZENU_OT_look_at_camera(bpy.types.Operator):
    bl_label = 'Look At Camera'
    bl_idname = 'zenu.look_at_camera'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        global_location = context.scene.camera.location

        armature_obj = bpy.data.objects["Armature"]
        pose_bone = armature_obj.pose.bones[EYE_TARGET_NAME]

        armature_space_loc = armature_obj.matrix_world.inverted() @ global_location

        pose_bone.location = pose_bone.bone.matrix_local.inverted() @ armature_space_loc
        return {'FINISHED'}


class ZENU_PT_character(RiftBasePanel):
    bl_label = 'Character'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_look_at_camera.bl_idname)
        layout.operator(ZENU_OT_generate_presets.bl_idname)

        control: CharacterControl = context.active_object.data.rift_character_control
        box = layout.column(align=True)
        box.scale_y = 1.5
        box.prop(control, 'eye_preset', text='')
        box.prop(control, 'eye_open', text='')

        box = layout.column(align=True)
        box.scale_y = 1.5
        box.prop(control, 'mouth_preset', text='')
        box.prop(control, 'mouth_open', text='')

        layout.prop(control, 'armature_object', text='')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_look_at_camera,
    ZENU_OT_generate_presets,
    CharacterControl,
    ZENU_PT_character,
))


def register():
    reg()

    bpy.types.Armature.rift_character_control = bpy.props.PointerProperty(type=CharacterControl)


def unregister():
    unreg()

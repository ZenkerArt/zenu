import uuid
from typing import Union

import bpy


class ExportPointSettings(bpy.types.PropertyGroup):
    is_default: bpy.props.BoolProperty(default=False)
    name: bpy.props.StringProperty(name='Name')
    uuid: bpy.props.StringProperty()
    file_type: bpy.props.EnumProperty(items=(
        ('FBX', 'FBX', ''),
        ('OBJ', 'OBJ', ''),
    ), name='File Type')

    # ------- FBX -------
    fbx_apply_modifiers: bpy.props.BoolProperty(name='Apply Modifiers', default=True)
    fbx_apply_transforms: bpy.props.BoolProperty(name='Apply Transform', default=False)

    # ------- FBX Animation -------
    fbx_use_leaf_bones: bpy.props.BoolProperty(name='Add Leaf Bones', default=False)
    fbx_only_deform_bones: bpy.props.BoolProperty(name='Only Deform Bones', default=True)
    fbx_bake_animation: bpy.props.BoolProperty(name='Bake Animation', default=True)
    fbx_key_all_bones: bpy.props.BoolProperty(name='Key All Bones', default=True)
    fbx_nla_strips: bpy.props.BoolProperty(name='NLA Strips', default=True)
    fbx_all_actions: bpy.props.BoolProperty(name='All Actions', default=False)
    fbx_force_start_end_keying: bpy.props.BoolProperty(name='Force Start/End Keying', default=True)

    @staticmethod
    def add_item() -> 'ExportPointSettings':
        item = bpy.context.scene.zenu_export_points_settings.add()
        item.uuid = uuid.uuid4().hex
        return item

    @classmethod
    def get_default_export_settings(cls) -> 'ExportPointSettings':
        for i in bpy.context.scene.zenu_export_points_settings:
            if i.is_default:
                return i

        item = cls.add_item()
        item.name = 'Default'
        item.is_default = True
        return item

    @staticmethod
    def get_by_index(index: int) -> 'ExportPointSettings':
        return bpy.context.scene.zenu_export_points_settings[index]

    @staticmethod
    def get_by_uuid(uuid: str) -> Union['ExportPointSettings', None]:
        for i in bpy.context.scene.zenu_export_points_settings:
            if i.uuid == uuid:
                return i

        return None

    @classmethod
    def get_active(cls):
        return cls.get_by_index(bpy.context.scene.zenu_export_points_settings_index)


class ZENU_OT_add_export_settings(bpy.types.Operator):
    bl_label = 'Add Export Settings'
    bl_idname = 'zenu.add_export_settings'

    def execute(self, context: bpy.types.Context):
        item = ExportPointSettings.add_item()
        item.name = 'Export Settings'
        return {'FINISHED'}


class ZENU_OT_remove_export_settings(bpy.types.Operator):
    bl_label = 'Remove Export Settings'
    bl_idname = 'zenu.remove_export_settings'

    def execute(self, context: bpy.types.Context):
        context.scene.zenu_export_points_settings.remove(context.scene.zenu_export_points_settings_index)

        if context.scene.zenu_export_points_settings_index < 1:
            return {'FINISHED'}

        context.scene.zenu_export_points_settings_index -= 1
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_add_export_settings,
    ZENU_OT_remove_export_settings,
    ExportPointSettings,
))


def register():
    reg()

    bpy.types.Scene.zenu_export_points_settings = bpy.props.CollectionProperty(
        type=ExportPointSettings)
    bpy.types.Scene.zenu_export_points_settings_index = bpy.props.IntProperty()


def unregister():
    unreg()

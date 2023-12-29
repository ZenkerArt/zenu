import bpy
from . import operators, panels, property_groups
from .physic_presets import physic_presets

reg, unreg = bpy.utils.register_classes_factory((
    *property_groups.classes,
    *operators.classes,
    *panels.classes,
))

  
def on_update_active_physic(self, context: bpy.types.Context):
    index: int = self.physic_group_active
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects[index]
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def physic_presets_list(self, context: bpy.types.Context):
    return [(i.name.upper(), i.name, '') for i in physic_presets]


def register():
    reg()
    bpy.types.Scene.physic_setting = bpy.props.PointerProperty(type=property_groups.PhysicSettingScene)
    bpy.types.Object.physic_setting = bpy.props.PointerProperty(type=property_groups.PhysicSetting)
    bpy.types.Scene.physic_group_active = bpy.props.IntProperty(update=on_update_active_physic)

    bpy.types.Scene.physic_presets = bpy.props.EnumProperty(items=physic_presets_list)


def unregister():
    unreg() 

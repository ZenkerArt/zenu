import bpy
from bpy.types import Context
from .utils import get_cloth
from ..base_panel import BasePanel

TAG_GLOBAL = 'GLOBAL'
TAG_LOCAL = 'LOCAL'


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


def aplay_scene_cloth_settings():
    for i in bpy.context.scene.objects:
        apply_object_cloth_settings(i)


def scene_settings_update(self: 'PhysicSetting', context: Context):
    aplay_scene_cloth_settings()


def object_settings_update(self: 'PhysicSetting', context: Context):
    apply_object_cloth_settings(context.active_object)


class PhysicSetting(bpy.types.PropertyGroup):
    start: bpy.props.IntProperty(name='Start Offset', update=object_settings_update)
    end: bpy.props.IntProperty(name='End Offset', update=object_settings_update)
    ignore: bpy.props.BoolProperty(name='Ignore')


class PhysicSettingScene(bpy.types.PropertyGroup):
    start: bpy.props.IntProperty(name='Start', update=scene_settings_update)
    end: bpy.props.IntProperty(name='End', update=scene_settings_update)


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
    bl_label = 'Rest Time'
    bl_idname = 'zenu.physic_bake_object'
    end: bpy.props.BoolProperty()
    type: bpy.props.EnumProperty(items={
        ('bake', 'Bake', ''),
        ('free', 'Free', ''),
        ('frame', 'Frame', ''),
    })

    @classmethod
    def poll(cls, context: Context):
        return get_cloth(context.active_object) is not None

    def execute(self, context: 'Context'):
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
            print('123')
        return {'FINISHED'}


class ZENU_OT_physic_rest_time_scene(bpy.types.Operator):
    bl_label = 'Rest Time'
    bl_idname = 'zenu.physic_rest_end_time_scene'
    end: bpy.props.BoolProperty()

    def execute(self, context: 'Context'):
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
    def poll(cls, context: 'Context'):
        return get_cloth(context.active_object) is not None

    def execute(self, context: 'Context'):
        if self.end:
            context.active_object.physic_setting.end = 0
        else:
            context.active_object.physic_setting.start = 0
        return {'FINISHED'}


class ZENU_PT_physic(BasePanel):
    bl_label = 'Physic'

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.scale_y = 1.5
        row.prop(context.scene, 'toggle_physic', icon='RESTRICT_VIEW_ON', text='Simulation')
        row = layout.row()
        row.scale_y = 1.5
        row.operator(ZENU_OT_physic_select_all.bl_idname, icon='RESTRICT_SELECT_OFF')


class ZENU_PT_physic_bake_active(BasePanel):
    bl_label = 'Bake Settings'
    bl_parent_id = 'ZENU_PT_physic'

    @classmethod
    def poll(cls, context: Context):
        return get_cloth(context.active_object) is not None

    def draw(self, context: 'Context'):
        layout = self.layout
        cloth = get_cloth(context.active_object)
        cache = cloth.point_cache

        col = layout.column_flow(align=True)
        col.enabled = True
        if cache.is_baked is True:
            col.operator(ZENU_OT_physic_bake_object.bl_idname, text="Delete Bake").type = 'free'
        else:
            col.operator(ZENU_OT_physic_bake_object.bl_idname, text="Bake").type = 'bake'
        col.operator(ZENU_OT_physic_bake_object.bl_idname, text="Calculate to Frame").type = 'frame'

        settings = context.active_object.physic_setting
        sp = layout.column_flow(align=True)
        grid = sp.grid_flow(columns=2, align=True)
        grid.prop(settings, 'start')
        grid.prop(settings, 'end')
        grid.operator(ZENU_OT_physic_rest_time_object.bl_idname, text='', icon='PANEL_CLOSE').end = False
        grid.operator(ZENU_OT_physic_rest_time_object.bl_idname, text='', icon='PANEL_CLOSE').end = True
        sp.prop(settings, 'ignore', icon='PANEL_CLOSE')
        sp = layout.split(align=True)
        sp.prop(cloth, 'show_viewport')
        sp.prop(cloth, 'show_render')
        layout.label(text=f'{cache.frame_start}:{cache.frame_end}')


class ZENU_PT_physic_bake_global(BasePanel):
    bl_label = 'Bake Global'
    bl_parent_id = 'ZENU_PT_physic'

    def draw(self, context: 'Context'):
        layout = self.layout
        col = layout.column_flow(align=True)
        col.operator("ptcache.bake_all", text="Bake All Dynamics").bake = True
        col.operator("ptcache.free_bake_all", text="Delete All Bakes")
        col.operator("ptcache.bake_all", text="Update All to Frame").bake = False

        settings = context.scene.physic_setting
        sp = layout.grid_flow(align=True, columns=2)
        sp.prop(settings, 'start')
        sp.prop(settings, 'end')
        sp.operator(ZENU_OT_physic_rest_time_scene.bl_idname, text='', icon='PANEL_CLOSE').end = False
        sp.operator(ZENU_OT_physic_rest_time_scene.bl_idname, text='', icon='PANEL_CLOSE').end = True


def set_viewport_display(state: bool):
    context = bpy.context
    for obj in context.scene.objects:
        cloth = get_cloth(obj)
        if cloth is None:
            continue

        cloth.show_viewport = state
        cloth.show_render = state


def view_display_update(self, context):
    set_viewport_display(context.scene.toggle_physic)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_physic_rest_time_scene,
    ZENU_OT_physic_rest_time_object,
    ZENU_OT_physic_bake_object,
    ZENU_OT_physic_select_all,
    ZENU_PT_physic,
    ZENU_PT_physic_bake_active,
    ZENU_PT_physic_bake_global,
    PhysicSetting,
    PhysicSettingScene
))


def register():
    reg()
    bpy.types.Scene.physic_setting = bpy.props.PointerProperty(type=PhysicSettingScene)
    bpy.types.Object.physic_setting = bpy.props.PointerProperty(type=PhysicSetting)

    bpy.types.Scene.toggle_physic = bpy.props.BoolProperty(update=view_display_update, default=True)


def unregister():
    unreg()

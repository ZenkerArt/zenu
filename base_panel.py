import bpy
from .utils import is_type


class BasePanelProperty(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_category = 'Zenu'
    pass


class BasePanel(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Zenu'
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_toggle(self, data, prop: str, text: str = '',
                    on_icon: str = 'RESTRICT_VIEW_ON',
                    off_icon: str = 'RESTRICT_VIEW_OFF',
                    invert_icon: bool = False,
                    layout: bpy.types.UILayout = None):
        layout = layout or self.layout

        if invert_icon:
            tmp = on_icon
            on_icon = off_icon
            off_icon = tmp

        layout.prop(data, prop,
                    icon=on_icon if getattr(data, prop, False) else off_icon,
                    text=text)


class BasePanelOnlyArmature(BasePanel):
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Armature)

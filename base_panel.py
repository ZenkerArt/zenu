import bpy


class BasePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Bone'
    bl_context = 'objectmode'

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

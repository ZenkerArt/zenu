import os

from ...utils import is_type
from ...base_panel import BasePanel
import bpy


class ZENU_OT_make_asset_icon_from_viewport(bpy.types.Operator):
    bl_label = 'Make Asset'
    bl_idname = 'zenu.make_asset_icon_from_viewport'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        obj: bpy.types.Object = context.active_object
        try:
            return obj.animation_data.action is not None
        except AttributeError:
            return False

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        action = obj.animation_data.action

        if action.asset_data is None:
            action.asset_mark()

        show_overlays = context.space_data.overlay.show_overlays
        context.space_data.overlay.show_overlays = False

        res_x = bpy.context.scene.render.resolution_x
        res_y = bpy.context.scene.render.resolution_y

        prev_file_format = bpy.context.scene.render.image_settings.file_format

        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.resolution_x = 128
        bpy.context.scene.render.resolution_y = 128

        bpy.ops.render.opengl(write_still=True)

        context.space_data.overlay.show_overlays = show_overlays
        bpy.context.scene.render.image_settings.file_format = prev_file_format
        bpy.context.scene.render.resolution_x = res_x
        bpy.context.scene.render.resolution_y = res_y

        file = bpy.path.abspath('//preview.png')
        bpy.data.images["Render Result"].save_render(file)

        with bpy.context.temp_override(id=action):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=file)

        os.remove(file)
        return {'FINISHED'}


class ZENU_PT_asset_browser_utils(BasePanel):
    bl_label = "Asset Browser"
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        text = 'Update Icon'
        try:
            if obj.animation_data:
                action = obj.animation_data.action
                if action.asset_data is None:
                    text = 'Make Asset'
        except AttributeError:
            pass

        layout.operator(ZENU_OT_make_asset_icon_from_viewport.bl_idname, text=text)


register, unregister = bpy.utils.register_classes_factory((
    ZENU_PT_asset_browser_utils,
    ZENU_OT_make_asset_icon_from_viewport
))

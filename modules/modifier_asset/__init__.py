import os

import bpy
from bpy.types import ToolSettings
from ...base_panel import BasePanel


def render_object(obj: bpy.types.Object, camera: bpy.types.Object, file_path: str, depsgraph):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    camera.location, fo = camera.camera_fit_coords(depsgraph, [co for corner in obj.bound_box for co in corner])
    camera.location += obj.location
    camera.data.ortho_scale = fo + .5

    res_x = bpy.context.scene.render.resolution_x
    res_y = bpy.context.scene.render.resolution_y

    prev_file_format = bpy.context.scene.render.image_settings.file_format

    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.resolution_x = 128
    bpy.context.scene.render.resolution_y = 128

    bpy.ops.render.opengl(write_still=True)

    bpy.context.scene.render.image_settings.file_format = prev_file_format
    bpy.context.scene.render.resolution_x = res_x
    bpy.context.scene.render.resolution_y = res_y

    file = bpy.path.abspath(file_path)
    bpy.data.images["Render Result"].save_render(file)


class ZENU_OT_add_modifier_asset(bpy.types.Operator):
    bl_label = 'Add Modifier Asset'
    bl_idname = 'zenu.add_modifier_asset'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        bpy.context.space_data.overlay.show_overlays = False

        obj = context.active_object
        obj.asset_mark()
        obj.asset_data.tags.new('MOD_ASSET', skip_if_exists=True)

        camera = context.scene.camera
        deph = context.evaluated_depsgraph_get()
        file = bpy.path.abspath('//render.jpg')
        render_object(obj, camera, file, deph)

        with bpy.context.temp_override(id=obj):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=file)

        return {'FINISHED'}


class ZENU_OT_apply_asset_mod(bpy.types.Operator):
    bl_label = 'Apply Asset Mod'
    bl_idname = 'zenu.apply_asset_mod'

    def execute(self, context: bpy.types.Context):
        shell: bpy.types.AssetRepresentation = context.asset
        obj: bpy.types.Object = bpy.context.object
        active_object = shell.metadata.id_data

        for mod_src in active_object.modifiers:
            mod_dst = obj.modifiers.get(mod_src.name, None)

            if not mod_dst:
                mod_dst = obj.modifiers.new(mod_src.name, mod_src.type)

            if mod_src.type == 'BEVEL':
                mod_src: bpy.types.BevelModifier
                mod_dst: bpy.types.BevelModifier

                points = mod_dst.custom_profile.points

                while len(points) > 2:
                    points.remove(points[1])

                for p in mod_src.custom_profile.points[1:-1]:
                    point = mod_dst.custom_profile.points.add(p.location.x, p.location.y)
                    point.handle_type_1 = p.handle_type_1
                    point.handle_type_2 = p.handle_type_2

            properties = [p.identifier for p in mod_src.bl_rna.properties
                          if not p.is_readonly]

            for prop in properties:
                setattr(mod_dst, prop, getattr(mod_src, prop))

        return {'FINISHED'}


class ZENU_PT_modifier_asset(BasePanel):
    bl_label = 'Modifier Asset'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_add_modifier_asset.bl_idname)


class VIEW3D_AST_modifier_asset(bpy.types.AssetShelf):
    bl_space_type = "VIEW_3D"
    bl_options = {'NO_ASSET_DRAG'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode == 'OBJECT'

    @classmethod
    def asset_poll(cls, asset: bpy.types.AssetRepresentation) -> bool:
        return asset.metadata.tags.get('MOD_ASSET')

    @classmethod
    def draw_context_menu(cls, context: bpy.types.Context, asset: bpy.types.AssetRepresentation,
                          layout: bpy.types.UILayout):
        if asset.metadata.tags.get('MOD_ASSET'):
            layout.operator(ZENU_OT_apply_asset_mod.bl_idname)
        else:
            pass


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_modifier_asset,
    ZENU_OT_add_modifier_asset,
    ZENU_OT_apply_asset_mod,
    VIEW3D_AST_modifier_asset,
))


def register():
    reg()


def unregister():
    unreg()

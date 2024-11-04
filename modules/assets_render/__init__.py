import os
import pickle
from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO

import numpy as np

import bpy
from bl_ui_utils.layout import operator_context
from mathutils import Vector
from ..rig.shapes import get_shape
from ...base_panel import BasePanel
from ...utils import get_path_to_asset


def render_object(obj: bpy.types.Object, camera: bpy.types.Object, file_path: str, depsgraph):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    camera.location, fo = camera.camera_fit_coords(depsgraph, [co for corner in obj.bound_box for co in corner])
    camera.location += obj.location
    camera.data.ortho_scale = fo + .1

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


@dataclass
class Shape:
    shape_index: int
    category_index: int
    name: str
    file: str

    @property
    def absolute_path(self) -> str:
        return get_path_to_asset(self.file)

    @property
    def label(self):
        return self.name.replace('WGT-', '')


@dataclass
class ShapeCategory:
    name: str


@dataclass
class ShapesConfig:
    # categories: dict[str, ShapeCategory] = field(default_factory=list)
    shapes: list[Shape] = field(default_factory=list)


class ZENU_OT_render_object(bpy.types.Operator):
    bl_label = 'Create Shape Collection'
    bl_idname = 'zenu.render_object'

    def execute(self, context: bpy.types.Context):
        # obj = context.active_object
        depsgraph = bpy.context.evaluated_depsgraph_get()
        objs = context.selected_objects
        shapes_conf = ShapesConfig()
        collections = Counter()

        for index, obj in enumerate(objs):
            for i in objs:
                i.hide_set(True)

            obj.hide_set(False)
            category_index = -1
            try:
                collection = obj.users_collection[0]
                collections[collection.name] += 1
                category_index = collections[collection.name]
            except IndexError:
                pass

            shapes_conf.shapes.append(Shape(
                category_index=category_index,
                name=obj.name,
                file=f'icons/{obj.name}.png',
                shape_index=index
            ))
            render_object(obj, context.scene.camera, f'//icons/{obj.name}.png', depsgraph)

        with open(get_path_to_asset('shapeconf.shapes'), mode='wb+') as fs:
            fs.write(pickle.dumps(shapes_conf))

        for i in objs:
            i.hide_set(False)
        return {'FINISHED'}


class ZENU_OT_create_assets(bpy.types.Operator):
    bl_label = 'Create Assets'
    bl_idname = 'zenu.create_assets'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        # obj = context.active_object
        objs = context.selected_objects

        for obj in objs:
            for i in objs:
                i.hide_set(True)

            obj.hide_set(False)

            obj.asset_mark()
            obj.asset_data.tags.new('WIDGET', skip_if_exists=True)
            obj.asset_data['object_name'] = obj.name
            depsgraph = bpy.context.evaluated_depsgraph_get()

            file = bpy.path.abspath(f'//images/{obj.name}.png')
            render_object(obj, context.scene.camera, file, depsgraph)

            with bpy.context.temp_override(id=obj):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=file)

            # os.remove(file)

        for i in objs:
            i.hide_set(False)

        return {'FINISHED'}


class ZENU_OT_apply_widget(bpy.types.Operator):
    bl_label = 'Apply Widget'
    bl_idname = 'zenu.apply_widget'
    bl_options = {'UNDO'}

    # @classmethod
    # def poll(cls, context: 'Context') -> bool:
    # return bpy.ops.

    def execute(self, context: bpy.types.Context):
        shell: bpy.types.AssetRepresentation = context.asset
        shape = get_shape(shell.metadata['object_name'])

        for mod in shape.modifiers:
            shape.modifiers.remove(mod)

        for pose in context.selected_pose_bones:
            pose.custom_shape = shape

        return {'FINISHED'}


class VIEW3D_AST_pose_library(bpy.types.AssetShelf):
    bl_space_type = "VIEW_3D"
    bl_options = {'NO_ASSET_DRAG'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode == 'POSE'

    @classmethod
    def asset_poll(cls, asset: bpy.types.AssetRepresentation) -> bool:
        return asset.metadata.tags.get('WIDGET') or asset.id_type == 'ACTION'

    @classmethod
    def action_panel(cls, layout: bpy.types.UILayout):
        layout.operator("poselib.apply_pose_asset", text="Apply Pose").flipped = False
        layout.operator("poselib.apply_pose_asset", text="Apply Pose Flipped").flipped = True

        with operator_context(layout, 'INVOKE_DEFAULT'):
            layout.operator("poselib.blend_pose_asset", text="Blend Pose").flipped = False
            layout.operator("poselib.blend_pose_asset", text="Blend Pose Flipped").flipped = True

        layout.separator()
        props = layout.operator("poselib.pose_asset_select_bones", text="Select Pose Bones")
        props.select = True
        props = layout.operator("poselib.pose_asset_select_bones", text="Deselect Pose Bones")
        props.select = False

        layout.separator()
        layout.operator("asset.open_containing_blend_file")

    @classmethod
    def draw_context_menu(cls, context: bpy.types.Context, asset: bpy.types.AssetRepresentation,
                          layout: bpy.types.UILayout):
        # Make sure these operator properties match those used in `VIEW3D_PT_pose_library_legacy`.
        if asset.id_type == 'ACTION':
            cls.action_panel(layout)
        else:
            layout.operator(ZENU_OT_apply_widget.bl_idname)


class ZENU_PT_assets_render(BasePanel):
    bl_label = 'assets_render'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_render_object.bl_idname)
        layout.operator(ZENU_OT_create_assets.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_render_object,
    ZENU_OT_create_assets,
    ZENU_OT_apply_widget,
    ZENU_PT_assets_render,
    VIEW3D_AST_pose_library
))


def register():
    reg()


def unregister():
    unreg()

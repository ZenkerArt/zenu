import os.path
import pickle
from os import scandir

import bpy
from bl_ui_utils.layout import operator_context
from bpy.types import WindowManager, EnumProperty
from bpy.utils.previews import ImagePreviewCollection
from ..assets_render import ShapesConfig
from ..rig.bone_utils import bone_clone
from ...base_panel import BasePanel
from ...utils import check_mods, is_type, get_path_to_asset

PREFIX_DATA = 'zenu_prefix'
images = []
preview_collections = {}
pcoll: ImagePreviewCollection = None


def enum_previews_from_directory_items(self, context):
    enum_items = []

    if context is None:
        return enum_items

    if pcoll.my_previews:
        return pcoll.my_previews

    for index, shape in enumerate(shapes_conf.shapes):
        data = shape.label
        icon = pcoll.get(data)

        if not icon:
            thumb = pcoll.load(data, shape.absolute_path, 'IMAGE')
        else:
            thumb = pcoll[data]
        enum_items.append((shape.name, shape.label, shape.name, thumb.icon_id, shape.shape_index))

    pcoll.my_previews = enum_items
    return pcoll.my_previews


class ZENU_OT_mark_bone(bpy.types.Operator):
    bl_label = 'Mark Bone'
    bl_idname = 'zenu.mark_bone'
    bl_options = {'UNDO'}

    prefix: bpy.props.StringProperty()
    use_deform: bpy.props.BoolProperty(default=True)
    collection: bpy.props.StringProperty()
    color_palette: bpy.props.StringProperty()

    def get_collection(self, obj: bpy.types.Object, name: str):
        arm: bpy.types.Armature = obj.data
        collection = arm.collections.get(name)
        if collection is None:
            collection = arm.collections.new(name)

        return collection

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        collection = None

        if self.collection != '':
            collection = self.get_collection(obj, self.collection)

        for bone in context.selected_editable_bones:
            name = bone.name
            bone.use_deform = self.use_deform
            has_prefix = bone.get(PREFIX_DATA)

            if self.color_palette != '':
                bone.color.palette = self.color_palette

            if not name.startswith(self.prefix) and self.prefix != '':
                if has_prefix:
                    bone.name = name.replace(has_prefix, self.prefix)
                else:
                    bone.name = self.prefix + name

                bone[PREFIX_DATA] = self.prefix

            if collection is not None:
                for i in bone.collections:
                    i.unassign(bone)
                collection.assign(bone)
        return {'FINISHED'}


class ZENU_OT_bone_change_color(bpy.types.Operator):
    bl_label = 'Color Select'
    bl_idname = 'zenu.bone_change_color'
    color_palette: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        for bone in context.selected_editable_bones:
            bone.color.palette = self.color_palette
        return {'FINISHED'}


class ZENU_OT_duplicate_bone_with_scale(bpy.types.Operator):
    bl_label = 'Bone Duplicate With Scale Down'
    bl_idname = 'zenu.duplicate_bone_with_scale'
    bl_options = {'REGISTER', 'UNDO'}
    scale: bpy.props.FloatProperty(name='Scale', subtype='FACTOR', min=0, max=1, default=.5)
    parent: bpy.props.BoolProperty(name='Parent', default=True)
    parent_revers: bpy.props.BoolProperty(name='Parent Revers', default=False)

    def execute(self, context: bpy.types.Context):
        new_bones = []
        arm: bpy.types.Armature = context.active_object.data

        for bone in context.selected_editable_bones:
            new_bone = bone_clone(bone)
            new_bone.length = bone.length * self.scale

            if hasattr(bone, PREFIX_DATA):
                new_bone[PREFIX_DATA] = bone[PREFIX_DATA]

            if self.parent:
                b1 = bone
                b2 = new_bone

                if self.parent_revers:
                    tmp = b1
                    b1 = b2
                    b2 = tmp

                b1.parent = b2

            new_bones.append(new_bone)

        bpy.ops.armature.select_all(action='DESELECT')

        for i in new_bones:
            i.select_tail = True
            i.select_head = True
            i.select = True

        arm.edit_bones.active = new_bones[0]
        return {'FINISHED'}


class ZENU_PT_bone_utils(BasePanel):
    bl_label = 'Bone Utils'
    bl_context = ''

    def markers(self, layout: bpy.types.UILayout):
        row = layout.row(align=True)
        op = row.operator(ZENU_OT_mark_bone.bl_idname, text='DEF')
        op.use_deform = True
        op.collection = 'DEF'
        op.prefix = 'DEF-'
        op.color_palette = 'THEME02'

        op = row.operator(ZENU_OT_mark_bone.bl_idname, text='MCH')
        op.use_deform = False
        op.collection = 'MCH'
        op.prefix = 'MCH-'
        op.color_palette = 'THEME09'

        row = layout.row(align=True)
        op = row.operator(ZENU_OT_mark_bone.bl_idname, text='FK')
        op.use_deform = False
        op.collection = ''
        op.prefix = 'FK-'
        op.color_palette = ''

        op = row.operator(ZENU_OT_mark_bone.bl_idname, text='IK')
        op.use_deform = False
        op.collection = ''
        op.prefix = 'IK-'
        op.color_palette = ''

    def color_picker(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        grid = layout.grid_flow(align=True, even_rows=False)

        for value in context.active_bone.color.rna_type.properties['palette'].enum_items.values():
            selected = context.active_bone.color.palette == value.identifier

            op = grid.operator(ZENU_OT_bone_change_color.bl_idname, icon=value.icon, text='', depress=selected)
            op.color_palette = value.identifier

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        wm = context.window_manager

        row = layout.column()
        row.template_icon_view(wm, "my_previews", show_labels=True)

        if not check_mods('e') or not is_type(context.active_object, bpy.types.Armature):
            return

        self.markers(layout)
        layout.operator(ZENU_OT_duplicate_bone_with_scale.bl_idname)

        panel, body = layout.panel("my_panel_id", default_closed=False)
        panel.label(text="Color Picker")
        if body:
            self.color_picker(context, body)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_mark_bone,
    ZENU_OT_bone_change_color,
    ZENU_OT_duplicate_bone_with_scale,
    ZENU_PT_bone_utils,
))


def register():
    global pcoll

    WindowManager.my_previews = bpy.props.EnumProperty(
        items=enum_previews_from_directory_items,
    )

    pcoll = bpy.utils.previews.new()
    pcoll.my_previews = ()
    preview_collections["main"] = pcoll

    reg()


def unregister():
    bpy.utils.previews.remove(pcoll)
    unreg()

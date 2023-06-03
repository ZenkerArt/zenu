import bpy
from .base_clasess import ObjectDrawer, ArmatureDrawer
from ...armature_operators import ZENU_OT_align_bone
from ...shape_key_bind import ZENU_OT_open_bind_shape_key
from ...utils_panel import ZENU_OT_change_display_type
from ....utils import is_type


class ObjectProperties(ObjectDrawer):

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object
        if self.is_object_mode and is_type(obj, bpy.types.Mesh):
            row = layout.row(align=True)
            row.scale_x = .5
            row.operator('object.shade_smooth', text='Smooth')
            row.operator('object.shade_flat', text='Flat')
            row.prop(obj.data, 'use_auto_smooth', text='Auto')

        row = layout.row(align=True)
        ZENU_OT_change_display_type.button(row, 'WIRE')
        ZENU_OT_change_display_type.button(row, 'TEXTURED')

        if self.is_object_mode:
            op = layout.operator('object.origin_set', text='Origin To Geometry')
            op.type = 'ORIGIN_GEOMETRY'
            op.center = 'MEDIAN'


class ArmatureProperties(ArmatureDrawer):

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        if self.is_edit:
            layout.operator('armature.symmetrize')
            op = layout.operator('armature.autoside_names', text='Auto L/R')
            op.type = 'XAXIS'
            layout.operator(ZENU_OT_align_bone.bl_idname)

        if self.is_pose:
            layout.operator('pose.select_mirror')
            layout.operator(ZENU_OT_open_bind_shape_key.bl_idname)

    def draw_submenu(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        arm = context.active_object.data
        layout.row(align=True).prop(arm, 'pose_position', expand=True)


classes = (
    ObjectProperties,
    ArmatureProperties
)

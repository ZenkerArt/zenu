import bpy
from .base_clasess import ArmatureDrawer, ObjectDrawer


def default_overlays(context: bpy.types.Context, layout: bpy.types.UILayout):
    obj = context.active_object
    if not obj:
        return

    layout.prop(obj, 'show_in_front')


class ObjectOverlays(ObjectDrawer):
    def draw(self, context: bpy.types.Context, layout):
        obj = context.active_object

        layout.prop(context.space_data.overlay, 'show_face_orientation')

        if not self.is_edit:
            layout.prop(obj, 'show_wire')

        if self.is_edit:
            layout.prop(context.space_data.overlay, 'show_weight', text='Weights')


class ArmatureOverlays(ArmatureDrawer):

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object
        arm: bpy.types.Armature = obj.data

        layout.prop(arm, 'show_names', text='Names')
        layout.prop(arm, 'show_axes', text='Axes')

    def draw_submenu(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        obj = context.active_object
        layout.row(align=True) \
            .prop(obj.data, 'display_type', text='Type', expand=True)


classes = (
    default_overlays,
    ObjectOverlays,
    ArmatureOverlays
)

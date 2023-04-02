# TODO: Сделать быстрое создание лоу-поли для мема со скелетом
# TODO: Быстрое создание иерархий коллекций
import bpy
from bpy.types import Context
from ..base_panel import BasePanel
from ..utils import check_mods


class ZENU_OT_change_display_type(bpy.types.Operator):
    bl_label = 'Change Display Type'
    bl_idname = 'zenu.change_display_type'
    type: bpy.props.StringProperty()

    @staticmethod
    def button(layout: bpy.types.UILayout, ty: str, text: str = None):
        text = text or ty.title()
        layout.operator(ZENU_OT_change_display_type.bl_idname,
                        depress=ty == bpy.context.active_object.display_type,
                        text=text).type = ty.upper()

    @classmethod
    def poll(cls, context: 'Context'):
        # if context.active_object is None:
        #     return

        return context.active_object

    def execute(self, context: Context):
        context.active_object.display_type = self.type
        return {'FINISHED'}


class ZENU_PT_utils(BasePanel):
    bl_label = 'Utils'
    bl_context = ''

    @classmethod
    def poll(cls, context: 'Context'):
        return check_mods('opes')

    def draw(self, context: Context):
        layout = self.layout


class ZENU_PT_object_property(BasePanel):
    bl_label = 'Object Props'
    bl_parent_id = 'ZENU_PT_utils'
    bl_context = ''

    @classmethod
    def poll(cls, context: Context):
        return context.active_object

    def draw(self, context: Context):
        obj = context.active_object
        obj_type = obj.type

        is_dupli = (obj.instance_type != 'NONE')
        is_geometry = (obj_type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'CURVES', 'POINTCLOUD'})

        col = self.layout.column_flow(align=True)
        self.draw_toggle(context.active_object, 'show_in_front', text='In Front', layout=col, invert_icon=True)
        if is_geometry or is_dupli:
            self.draw_toggle(obj, "show_wire", text='Wire', layout=col, invert_icon=True)
        if obj.mode == 'EDIT':
            self.draw_toggle(context.space_data.overlay, 'show_weight', text='Weights', layout=col, invert_icon=True)
        wire = col.row(align=True)
        ZENU_OT_change_display_type.button(wire, 'WIRE')
        ZENU_OT_change_display_type.button(wire, 'TEXTURED')

        self.draw_arm(context)

    def draw_arm(self, context: Context):
        arm = context.active_object.data
        if not isinstance(arm, bpy.types.Armature):
            return
        col = self.layout.column_flow(align=True)
        col.prop(arm, 'display_type', text='')
        self.draw_toggle(arm, 'show_names', text='Bones Names', layout=col)
        self.draw_toggle(arm, 'show_axes', text='Bones Axis', layout=col)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_utils,
    ZENU_PT_object_property,
    ZENU_OT_change_display_type,
))


def register():
    reg()


def unregister():
    unreg()

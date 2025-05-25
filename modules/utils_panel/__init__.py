import json

import bpy
from bpy.types import Context




class ZENU_OT_change_display_type(bpy.types.Operator):
    bl_label = 'Change Display Type'
    bl_idname = 'zenu.change_display_type'
    type: bpy.props.StringProperty()

    @staticmethod
    def button(layout: bpy.types.UILayout, ty: str, text: str = None):
        if not bpy.context or not bpy.context.active_object:
            return

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


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_change_display_type,
))


def register():
    reg()


def unregister():
    unreg()

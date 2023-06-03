import bpy


class ZENU_OT_move_pivot(bpy.types.Operator):
    bl_label = 'Move Pivot'
    bl_idname = 'zenu.move_pivot'

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}


classes = (
    ZENU_OT_move_pivot,
)


def draw(context: bpy.types.Context, layout: bpy.types.UILayout):
    pass

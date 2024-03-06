import bpy


class ExportPoint(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(subtype='FILE_NAME')
    path: bpy.props.StringProperty(subtype='DIR_PATH')

    file_type: bpy.props.EnumProperty(items=(
        ('FBX', 'FBX', ''),
        ('OBJ', 'OBJ', ''),
    ), name='File Type')


class ZENU_OT_add_export_point(bpy.types.Operator):
    bl_label = 'Add Export Point'
    bl_idname = 'zenu.add_export_point'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        item = context.scene.zenu_export_points.add()
        item.name = 'File'
        context.scene.zenu_export_points_index = len(context.scene.zenu_export_points) - 1
        return {'FINISHED'}


class ZENU_OT_remove_export_point(bpy.types.Operator):
    bl_label = 'Remove Export Point'
    bl_idname = 'zenu.remove_export_point'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        context.scene.zenu_export_points.remove(context.scene.zenu_export_points_index)

        if context.scene.zenu_export_points_index < 1:
            return {'FINISHED'}

        context.scene.zenu_export_points_index -= 1
        return {'FINISHED'}


classes = (
    ZENU_OT_add_export_point,
    ZENU_OT_remove_export_point,
    ExportPoint
)

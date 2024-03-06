import os
from collections import defaultdict

import bpy
from bpy_extras.io_utils import ExportHelper


class BaseExport(bpy.types.Operator, ExportHelper):
    export_name: bpy.props.StringProperty(
        name='Export Name Template',
        default='$_export.fbx'
    )
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='DIR_PATH',
    )

    def invoke(self, context, _event):
        import os
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            self.filepath = os.path.join(blend_filepath, 'file.fbx')
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export(self, objs: list[bpy.types.Object], name: str):
        with bpy.context.temp_override(selected_objects=objs):
            path = os.path.join(os.path.dirname(self.filepath), self.export_name.replace('$', name))
            bpy.ops.export_scene.fbx(filepath=path, use_selection=True)


class ZENU_OT_export_by_name(BaseExport):
    bl_label = 'Export By Name'
    bl_idname = 'zenu.export_by_name'



    filename_ext = ".fbx"

    def execute(self, context: bpy.types.Context):
        for obj in context.selected_objects:
            self.export([obj], obj.name)
        return {'FINISHED'}


class ZENU_OT_export_by_collection(BaseExport):
    bl_label = 'Export By Collection'
    bl_idname = 'zenu.export_by_collection'

    filename_ext = ".fbx"

    def execute(self, context: bpy.types.Context):
        objs = defaultdict(list)

        for obj in context.selected_objects:
            try:
                collection = obj.users_collection[0]
            except IndexError:
                continue

            objs[collection.name].append(obj)

        for key, lst in objs.items():
            self.export(lst, key)
        return {'FINISHED'}


classes = (
    ZENU_OT_export_by_name,
    ZENU_OT_export_by_collection
)

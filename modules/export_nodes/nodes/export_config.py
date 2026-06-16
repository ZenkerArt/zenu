import json
import os
import shutil

import bpy

from .base_node import BaseNode
from .. import node_categories
from ..sockets.any_socket import AnySocketType
from ..sockets.file_socket import FileSocketType, FileExportPromise


class ExportConfig(BaseNode):
    bl_idname = "ExportConfig"
    bl_label = "Export Config"

    version: bpy.props.EnumProperty(items=(
        ('1.0', 'Version 1.0', ''),
    ), default='1.0', name='Versions')

    path: bpy.props.StringProperty(subtype='DIR_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    file_name: bpy.props.StringProperty(subtype='FILE_NAME')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'version', text='')

        box = layout.box().row(align=True)
        box.prop(self, 'path', text='', placeholder='File Path')
        box.prop(self, 'file_name', text='', placeholder='File Name')

    def init(self, context):
        self.inputs.new(FileSocketType.bl_idname, 'files', use_multi_input=True)
        self.outputs.new(AnySocketType.bl_idname, 'execute')
        self.width = 300

    def compute(self, files: list[FileExportPromise], **inputs):
        path = bpy.path.abspath(self.path)
        folder = os.path.join(path, self.file_name)
        assets = os.path.join(folder, 'Assets')

        dct = {
            'version': self.version,
            'files': []
        }

        if not os.path.exists(folder):
            os.mkdir(folder)
        else:
            shutil.rmtree(folder)
            os.mkdir(folder)

        if not os.path.exists(assets):
            os.mkdir(assets)
        else:
            shutil.rmtree(assets)
            os.mkdir(assets)


        for file in files:
            dct['files'].append(file.export(assets, folder))

        with open(os.path.join(folder, 'manifest.json'), mode='w') as fs:
            fs.write(json.dumps(dct, indent=True))

        return {}


reg, unreg = bpy.utils.register_classes_factory((
    ExportConfig,
))


def register():
    node_categories.general.add_node(ExportConfig)
    reg()


def unregister():
    unreg()

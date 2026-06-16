import os.path

import bpy
from .base_node import BaseNode
from .. import node_categories
from ..sockets.character_equipment_socket import CharacterEquipTypeSocket, CharacterEquipData
from ..sockets.file_socket import FileExportPromise, FileSocketType
from hashlib import sha1


class CharacterEquipExportPromise(FileExportPromise):
    lst: list[CharacterEquipData]
    name: str

    def __init__(self, lst: list[CharacterEquipData], name: str):
        self.lst = lst
        self.name = name

    def export(self, path: str, root: str):
        bpy.context.view_layer.objects.active = None
        lst = list()

        folder = os.path.join(path, self.name)

        if not os.path.exists(folder):
            os.mkdir(folder)

        for i in self.lst:
            bpy.ops.object.select_all(action='DESELECT')
            i.object.select_set(True)

            file = os.path.join(folder, sha1(i.name.encode()).hexdigest())

            bpy.ops.export_scene.gltf(
                filepath=file,
                use_selection=True
            )

            lst.append({
                'path': os.path.relpath(file, root) + '.glb',
                'name': i.name,
                'characterName': i.armature.name,
            })

        return {
            'type': 'CharacterEquipSet',
            'name': self.name,
            'files': lst
        }

    def __repr__(self):
        return f'<{type(self).__name__} length={len(self.lst)}>'


class CharacterEquipExport(BaseNode):
    bl_idname = "CharacterEquipExport"
    bl_label = "Character Equipment Export"

    name: bpy.props.StringProperty()

    def draw_buttons(self, context, layout):
        box = layout.box()
        box.label(text='Name')
        box.prop(self, 'name', text='')

    def init(self, context):
        self.inputs.new(CharacterEquipTypeSocket.bl_idname, 'equip', use_multi_input=True)
        self.outputs.new(FileSocketType.bl_idname, 'equip')
        self.width = 200

    def compute(self, **inputs):
        return {
            'equip': CharacterEquipExportPromise(inputs['equip'], name=self.name)
        }


reg, unreg = bpy.utils.register_classes_factory((
    CharacterEquipExport,
))


def register():
    node_categories.character_equip.add_node(CharacterEquipExport)
    reg()


def unregister():
    unreg()

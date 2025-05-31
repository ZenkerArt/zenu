import gzip
import json
import os
import zipfile
from urllib.parse import urlparse, unquote

import py7zr

import bpy

from ...base_panel import BasePanel
from bpy_extras.io_utils import ImportHelper
import pip


# https://bitbucket.org/Diffeomorphic/import_daz/src/master/load_json.py
def loadJson(filepath, mustOpen=False, silent=False):
    def loadFromString(string):
        struct = {}
        jsonerr = None
        try:
            struct = json.loads(string)
            msg = None
        except json.decoder.JSONDecodeError as err:
            msg = ('JSON error while reading %s file\n"%s"\n%s' % (filetype, filepath, err))
            jsonerr = str(err)
        except UnicodeDecodeError as err:
            msg = ('Unicode error while reading %s file\n"%s"\n%s' % (filetype, filepath, err))
        return struct, msg, jsonerr

    def smashString(string, jsonerr):
        # Expecting value: line 14472 column 630 (char 619107)
        words = jsonerr.split("(char ")
        if len(words) == 2:
            nstring = words[1].split(")")[0]
            if nstring.isdigit():
                n1 = int(nstring)
                n = n1 - 1
                if len(string) < n:
                    print("Unknown error: %s" % jsonerr)
                    return None
                while string[n].isspace() and n > 0:
                    n -= 1
                if string[n] == ",":
                    print("Smashing character %d" % n)
                    return "%s %s" % (string[:n], string[n1:])
        return None

    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        msg = 'File does not exist:\n"%s"' % filepath
        if silent:
            return {}
        elif mustOpen:
            raise RuntimeError(msg)
        else:
            print(msg)
            return {}
    try:
        with gzip.open(filepath, 'rb') as fp:
            bytes = fp.read()
    except IOError:
        bytes = None

    if bytes:
        try:
            string = bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            string = bytes.decode("utf-16")
        filetype = "zipped"
    else:
        try:
            try:
                with open(filepath, 'r', encoding="utf-8-sig") as fp:
                    string = fp.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding="utf-16") as fp:
                    string = fp.read()
            filetype = "ascii"
        except IOError:
            string = None
        except UnicodeDecodeError:
            string = None
    if string is None:
        if not silent:
            print('Could not open file\n"%s"\n' % (filepath))
        return {}

    struct, msg, jsonerr = loadFromString(string)
    if jsonerr:
        try:
            string = smashString(string, jsonerr)
        except IndexError:
            string = ""
        if string:
            struct, msg, jsonerr = loadFromString(string)
    if msg and not silent:
        print(msg)
    return struct


class ZENU_OT_import_daz_properties_preset(bpy.types.Operator, ImportHelper):
    bl_label = 'Import Daz Properties Preset'
    bl_idname = 'zenu.import_daz_properties_preset'

    filter_glob: bpy.props.StringProperty(
        default="*.duf;",
        options={'HIDDEN'},
    )

    filename: bpy.props.StringProperty(maxlen=1024)
    directory: bpy.props.StringProperty(maxlen=1024)

    # files: bpy.props.CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)

    def execute(self, context: bpy.types.Context):
        file = str(os.path.join(self.directory, self.filename))
        js = loadJson(file)

        for i in js['scene']['animations']:
            url = urlparse(unquote(i['url']))
            value = i['keys']
            fragments = url.fragment.split('/')

            if 'materials' in fragments:
                continue

            key = url.fragment.split(':')[0].strip()
            # shape = context.active_object.get(key)
            shape: bpy.types.Mesh = context.active_object.data
            shape:bpy.types.ShapeKey = shape.shape_keys.key_blocks.get(key)
            # print(shape, key)
            if shape is not None:
                shape.value = value[0][1]
                # context.active_object[key] = value[0][1]
                # print(key, context.active_object[key], value)
        return {'FINISHED'}


class ZENU_PT_daz_help(BasePanel):
    bl_label = 'Daz Help'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        layout.operator(ZENU_OT_import_daz_properties_preset.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_daz_help,
    ZENU_OT_import_daz_properties_preset
))


def register():
    reg()


def unregister():
    unreg()

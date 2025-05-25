import json
import math
import os
import socket
import struct
from io import BytesIO

import bpy
from mathutils import Vector, Quaternion, Matrix

from ...base_panel import BasePanel


class ZENU_OT_load_from_unity(bpy.types.Operator):
    bl_label = 'Load From Unity'
    bl_idname = 'zenu.load_from_unity'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        data = json.loads(bpy.context.window_manager.clipboard)
        # data = {"IPD":0.054642483592033389,"cameraPos":{"x":4.014232635498047,"y":0.7262111306190491,"z":-5.187626361846924},"cameraCustom":{"x":-0.11146439611911774,"y":0.727434515953064,"z":-0.11973302066326142,"w":-0.6663922667503357},"cameraRotation":{"x":0.08978594094514847,"y":-0.7304271459579468,"z":0.11973308026790619,"w":0.6663922667503357},"cameraRotationLocal":{"x":0.08978594094514847,"y":-0.7304271459579468,"z":0.11973308026790619,"w":0.6663922667503357},"rotationEuler":{"x":0.0,"y":0.0,"z":0.0}}
        # data = {"IPD":0.0630037859082222,"cameraPos":{"x":-4.202420234680176,"y":0.8871870040893555,"z":5.204329967498779},"cameraRotation":{"x":0,"y":90,"z":90}}

        pos = data['cameraPos']
        pos = Vector((-pos['x'], -pos['z'], pos['y']))
        rotation_euler = data["rotationEuler"]
        rotation = data["cameraRotation"]
        rotation = Quaternion((rotation["w"], rotation["x"], rotation["z"], rotation["y"]))


        axis, angle = rotation.to_axis_angle()
        r = Matrix.Rotation(angle, 4, axis)
        r @= Matrix.Rotation(math.radians(-90), 4, 'X')
        # r *= Matrix.Rotation(math.radians(90), 4, 'Z')
        # r @= Matrix.Scale(-1, 4, (0, 1, 0))

        q = r.to_quaternion()
        e = q.to_euler()
        print(math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))
        context.active_object.location = pos

        context.active_object.data.stereo.interocular_distance = data['IPD']

        context.active_object.rotation_quaternion = Quaternion((q.w, q.x, q.z, q.y))
        bpy.ops.transform.rotate(value=3.14159, orient_axis='Z', orient_type='LOCAL')

        # context.active_object.rotation_euler = Vector((math.radians(rotation_euler['x']), math.radians(rotation_euler['y']), math.radians(rotation_euler['z'])))
        return {'FINISHED'}

class ZENU_OT_send_image(bpy.types.Operator):
    bl_label = 'Send Image'
    bl_idname = 'zenu.send_image'

    def execute(self, context: bpy.types.Context):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect(("127.0.0.1", 8888))

        bpy.context.scene.render.filepath = '//renderimage.png'
        bpy.ops.render.render(write_still=True)

        with open(bpy.path.abspath('//renderimage.png'), mode='rb') as fs:
            fs.seek(0, os.SEEK_END)
            content_length = fs.tell()
            fs.seek(0)
            s.send(struct.pack('i', content_length))
            s.send(fs.read())
            s.close()


        return {'FINISHED'}

class ZENU_PT_unity(BasePanel):
    bl_label = 'Unity'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_load_from_unity.bl_idname)
        layout.operator(ZENU_OT_send_image.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_load_from_unity,
    ZENU_OT_send_image,
    ZENU_PT_unity
))


def register():
    reg()


def unregister():
    unreg()

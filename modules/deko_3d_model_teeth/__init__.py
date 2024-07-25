import json

import bmesh
import bpy
from mathutils import Vector
from ...base_panel import BasePanel


class TeethSettings(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(subtype='FILE_PATH')
    step: bpy.props.FloatProperty(subtype='DISTANCE', min=0, max=1)


def get_teeth_settings(context: bpy.types.Context) -> TeethSettings:
    return context.scene.zenu_deko_teeth


class ZENU_OT_import_mesh(bpy.types.Operator):
    bl_label = 'Import'
    bl_idname = 'zenu.import_mesh'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        settings = get_teeth_settings(context)

        mesh = bpy.data.meshes.new("mesh")  # add a new mesh
        obj = bpy.data.objects.new("MyObject", mesh)  # add a new object using the mesh

        scene = context.scene
        col = context.view_layer.layer_collection.collection
        col.objects.link(obj)

        obj.select_set(True)
        bm = bmesh.new()

        with open(settings.path, mode='rb') as f:
            data = json.loads(f.read())
            for frame, verts in data:
                for vert in verts:
                    pos = Vector((vert[0], vert[1], frame * settings.step))
                    bm.verts.new(pos)

        # for v in [(0, 0, 0), (0, 0, 1)]:
        #     bm.verts.new(v)  # add a new vert

        # make the bmesh the object's mesh
        bm.to_mesh(mesh)
        bm.free()  # always do this when finished

        return {'FINISHED'}


class ZENU_PT_teeth_panel(BasePanel):
    bl_label = 'teeth_panel'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        teeth = get_teeth_settings(context)

        col = layout.column(align=True)
        col.prop(bpy.context.scene.unit_settings, 'length_unit', text='')
        col.prop(teeth, 'step', text='')
        col.prop(teeth, 'path', text='')
        col.operator(ZENU_OT_import_mesh.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_import_mesh,
    ZENU_PT_teeth_panel,
    TeethSettings
))


def register():
    reg()
    bpy.types.Scene.zenu_deko_teeth = bpy.props.PointerProperty(type=TeethSettings)


def unregister():
    unreg()

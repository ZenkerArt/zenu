import bmesh
import bpy
from mathutils import Vector
from ...base_panel import BasePanel


class ZENU_OT_unbevel(bpy.types.Operator):
    bl_label = 'Create Empty'
    bl_idname = 'zenu.create_empty'
    bl_options = {'UNDO'}

    def calc_box(self, bm: bmesh.types.BMesh):
        pass

    def execute(self, context: bpy.types.Context):
        obj = bpy.context.edit_object
        me: bpy.types.Mesh = obj.data
        bm = bmesh.from_edit_mesh(me)

        selected_verts = list(filter(lambda v: v.select, bm.verts))

        mid_point = Vector((0, 0, 0))
        for i in selected_verts:
            mid_point += i.co

        empty = bpy.data.objects.new('Empty', None)
        empty.location = mid_point / len(selected_verts)
        context.view_layer.layer_collection.collection.objects.link(empty)
        empty.select_set(True)

        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.parent_set(type='VERTEX_TRI')

        return {'FINISHED'}


class ZENU_PT_mesh_utils(BasePanel):
    bl_label = 'Mesh Utils'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_unbevel.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_mesh_utils,
    ZENU_OT_unbevel
))


def register():
    reg()


def unregister():
    unreg()

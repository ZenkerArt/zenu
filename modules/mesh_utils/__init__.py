import bmesh
import bpy
from mathutils import Vector
from ...base_panel import BasePanel


class ZENU_OT_unbevel(bpy.types.Operator):
    bl_label = 'Unbevel'
    bl_idname = 'zenu.unbevel'
    bl_options = {'UNDO'}

    def calc_box(self, bm: bmesh.types.BMesh):
        pass

    def execute(self, context: bpy.types.Context):
        obj = bpy.context.edit_object
        me: bpy.types.Mesh = obj.data
        bm = bmesh.from_edit_mesh(me)

        face = bm.faces.active
        corner_faces = []
        corner_points: list[tuple[bmesh.types.BMFace, bmesh.types.BMVert, bmesh.types.BMVert, bmesh.types.BMVert]] = []

        for vert in face.verts:
            for face_vert in vert.link_faces:
                vert_count = len(face_vert.verts)
                if vert_count == 3:
                    corner_faces.append(face_vert)

        for corner_face in corner_faces:
            pair = []
            main_vert = None
            for vert in corner_face.verts:
                if face not in vert.link_faces:
                    pair.append(vert)
                else:
                    main_vert = vert

            corner_points.append(tuple([corner_face, main_vert, *pair]))
            # corner_face.select = True

        verts = []
        for corner_vert in corner_points:
            corner_face, a, b, c = corner_vert
            center = face.calc_center_median()
            n_diff = (corner_face.normal - face.normal)

            if n_diff.x > 0:
                tan = face.calc_tangent_edge()
                n_up = face.normal.cross(tan)

                off = abs(c.co.z - b.co.z)
                tan *= -off

                if n_diff.z > 0:
                    n_up *= -off
                else:
                    n_up *= off

                print(off)
                bm.verts.new(Vector((b.co.x, b.co.y, b.co.z)) + tan)
                bm.verts.new(Vector((c.co.x, c.co.y, c.co.z)) + n_up)

            # p = Vector(())  # find_max(ys)
            # verts.append(bm.verts.new(p))
            # break

        # bm.faces.new(verts)

        # bm.to_mesh(me)
        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
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

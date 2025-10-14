import bmesh
import bpy
from mathutils import Vector, Matrix
from ...base_panel import BasePanel


def add_empty(name: str):
    empty = bpy.data.objects.get(name)

    if empty:
        return empty

    empty = bpy.data.objects.new(name, None)
    bpy.context.view_layer.layer_collection.collection.objects.link(empty)

    return empty

# https://blender.stackexchange.com/questions/187095/how-can-i-move-the-pivot-gizmo-to-0-0-0-in-a-python-script


def set_origin(ob, global_origin=Vector()):
    mw = ob.matrix_world
    o = mw.inverted() @ Vector(global_origin)
    ob.data.transform(Matrix.Translation(-o))
    mw.translation = global_origin


def apply_origin(obj: bpy.types.Object, origin: Vector):
    bbox_corners = [obj.matrix_world @
                    Vector(corner) for corner in obj.bound_box]

    main_pos = Vector(bbox_corners[2])
    dist_lr = abs((main_pos - bbox_corners[6]).length)
    dist_fb = abs((main_pos - bbox_corners[1]).length)
    dist_du = abs((main_pos - bbox_corners[3]).length)

    main_pos.x += dist_lr * origin.x
    main_pos.y -= dist_fb * origin.y
    main_pos.z -= dist_du * origin.z

    set_origin(obj, origin)


class ZENU_OT_rest_pivot(bpy.types.Operator):
    bl_label = 'Rest Pivot'
    bl_idname = 'zenu.reset_pivot'
    bl_options = {'UNDO'}
    pivot: bpy.props.FloatVectorProperty(name='Pivot', min=0, max=1)

    def execute(self, context: bpy.types.Context):
        # obj = context.active_object

        for obj in context.selected_objects:

            bbox_corners = [obj.matrix_world @
                            Vector(corner) for corner in obj.bound_box]

            main_pos = Vector(bbox_corners[2])
            dist_lr = abs((main_pos - bbox_corners[6]).length)
            dist_fb = abs((main_pos - bbox_corners[1]).length)
            dist_du = abs((main_pos - bbox_corners[3]).length)

            piv = Vector(self.pivot)

            main_pos.x += dist_lr * piv.x
            main_pos.y -= dist_fb * piv.y
            main_pos.z -= dist_du * piv.z

            set_origin(obj, main_pos)
        return {'FINISHED'}


class ZENU_OT_to_column(bpy.types.Operator):
    bl_label = 'To Column'
    bl_idname = 'zenu.to_column'
    bl_options = {'REGISTER', 'UNDO'}
    col: bpy.props.IntProperty(name='Columns', default=2, min=1)
    offset: bpy.props.FloatProperty(name='Offset', default=1, min=0)

    def execute(self, context: bpy.types.Context):
        # obj = context.active_object
        # prev_pos = Vector((0, 0, 0))
        for index, obj in enumerate(context.selected_objects):
            obj.location = Vector(((self.offset * (index % self.col)), self.offset * (index // self.col), 0))
            
        return {'FINISHED'}


class ZENU_PT_mesh_utils(BasePanel):
    bl_label = 'Mesh Utils'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column(align=True)

        row = col.row(align=True)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='')
        op.pivot = (0, 0, 1)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='')
        op.pivot = (.5, 0, 1)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='')
        op.pivot = (1, 0, 1)

        row = col.row(align=True)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='Left')
        op.pivot = (0, .5, 1)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='Center')
        op.pivot = (.5, .5, 1)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='Right')
        op.pivot = (1, .5, 1)

        row = col.row(align=True)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='')
        op.pivot = (0, 1, 1)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='')
        op.pivot = (.5, 1, 1)

        op = row.operator(ZENU_OT_rest_pivot.bl_idname, text='')
        op.pivot = (1, 1, 1)
        
        layout.operator(ZENU_OT_to_column.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_mesh_utils,
    ZENU_OT_to_column,
    ZENU_OT_rest_pivot
))


def register():
    reg()


def unregister():
    unreg()

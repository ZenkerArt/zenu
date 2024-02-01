import json

import bpy
from bpy.types import Context
from ...base_panel import BasePanel
from ...utils import check_mods


def point_cloud(ob_name, coords, edges=[], faces=[]):
    """Create point cloud object based on given coordinates and name.

    Keyword arguments:
    ob_name -- new object name
    coords -- float triplets eg: [(-1.0, 1.0, 0.0), (-1.0, -1.0, 0.0)]
    """

    # Create new mesh and a new object
    me = bpy.data.meshes.new(ob_name + "Mesh")
    ob = bpy.data.objects.new(ob_name, me)

    # Make a mesh from a list of vertices/edges/faces
    me.from_pydata(coords, edges, faces)

    # Display name and update the mesh
    ob.show_name = True
    me.update()
    return ob

class ZENU_OT_change_display_type(bpy.types.Operator):
    bl_label = 'Change Display Type'
    bl_idname = 'zenu.change_display_type'
    type: bpy.props.StringProperty()

    @staticmethod
    def button(layout: bpy.types.UILayout, ty: str, text: str = None):
        if not bpy.context or not bpy.context.active_object:
            return

        text = text or ty.title()
        layout.operator(ZENU_OT_change_display_type.bl_idname,
                        depress=ty == bpy.context.active_object.display_type,
                        text=text).type = ty.upper()

    @classmethod
    def poll(cls, context: 'Context'):
        # if context.active_object is None:
        #     return

        return context.active_object

    def execute(self, context: Context):
        context.active_object.display_type = self.type
        return {'FINISHED'}


class ZENU_OT_test_import(bpy.types.Operator):
    bl_label = 'Test Import'
    bl_idname = 'zenu.test_import'
    type: bpy.props.StringProperty()

    def execute(self, context: Context):
        with open(r'C:\Users\zenke\Desktop\Projects\scan\output.txt', 'r') as filehandle:
            arr = json.load(filehandle)

        mesh = []
        length = len(arr)
        for i in arr:
            index, locations = i
            for location in locations:
                mesh.append((location[0], location[1], 0.0025 * index))

            print(f'Import frame {index} / {length}')

        # Create the object
        pc = point_cloud("point-cloud", mesh)

        # Link object to the active collection
        bpy.context.collection.objects.link(pc)

        return {'FINISHED'}

class ZENU_OT_clean_vertex_groups(bpy.types.Operator):
    bl_label = 'Clean Vertex Group'
    bl_idname = 'zenu.clean_vertex_group'
    type: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh) and check_mods('o')

    def mesh_analise(self, obj: bpy.types.Object, vertices: bpy.types.MeshVertices):
        group_indexes = []

        for vert in vertices:
            for group in vert.groups:
                group_indexes.append(group.group)

        group_indexes = tuple(set(group_indexes))

        removed = 0
        groups = [i for i in obj.vertex_groups if i.index not in group_indexes]
        for group in groups:
            obj.vertex_groups.remove(group)
            removed += 1
        self.report({'INFO'}, f'Removed Groups {removed}')

    def execute(self, context: Context):
        depsgraph = context.evaluated_depsgraph_get()
        object_eval = context.active_object.evaluated_get(depsgraph)
        mesh: bpy.types.Mesh = object_eval.data

        current_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        self.mesh_analise(context.active_object, mesh.vertices)
        # bpy.ops.object.mode_set(mode=current_mode)
        return {'FINISHED'}


class ZENU_PT_utils(BasePanel):
    bl_label = 'Utils'
    bl_context = ''

    @classmethod
    def poll(cls, context: 'Context'):
        return check_mods('opesw')

    def draw(self, context: Context):
        layout = self.layout
        layout.operator(ZENU_OT_clean_vertex_groups.bl_idname)
        layout.operator(ZENU_OT_test_import.bl_idname)


class ZENU_PT_object_property(BasePanel):
    bl_label = 'Object Props'
    bl_parent_id = 'ZENU_PT_utils'
    bl_context = ''

    @classmethod
    def poll(cls, context: Context):
        return context.active_object

    def draw(self, context: Context):
        obj = context.active_object
        obj_type = obj.type

        is_dupli = (obj.instance_type != 'NONE')
        is_geometry = (obj_type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'CURVES', 'POINTCLOUD'})

        col = self.layout.column_flow(align=True)
        self.draw_toggle(context.active_object, 'show_in_front', text='In Front', layout=col, invert_icon=True)
        if is_geometry or is_dupli:
            self.draw_toggle(obj, "show_wire", text='Wire', layout=col, invert_icon=True)

        if obj.mode == 'EDIT':
            self.draw_toggle(context.space_data.overlay, 'show_weight', text='Weights', layout=col, invert_icon=True)

        wire = col.row(align=True)
        ZENU_OT_change_display_type.button(wire, 'WIRE')
        ZENU_OT_change_display_type.button(wire, 'TEXTURED')
        self.draw_toggle(context.space_data.overlay, 'show_face_orientation', text='Face Orientation',
                         layout=col, invert_icon=True)

        self.draw_arm(context)

    def draw_arm(self, context: Context):
        arm = context.active_object.data

        if not isinstance(arm, bpy.types.Armature):
            return
        col = self.layout.column_flow(align=True)
        col.prop(arm, 'display_type', text='')
        self.draw_toggle(arm, 'show_names', text='Bones Names', layout=col)
        self.draw_toggle(arm, 'show_axes', text='Bones Axis', layout=col)

        col.row().prop(arm, "pose_position", expand=True)

        if context.active_pose_bone:
            col.prop(context.active_pose_bone, "custom_shape", text='')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_utils,
    ZENU_OT_change_display_type,
    ZENU_OT_clean_vertex_groups,
    ZENU_OT_test_import
))


def register():
    reg()


def unregister():
    unreg()

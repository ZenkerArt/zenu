import bmesh
import bpy
import bpy_extras
from bpy_extras import bmesh_utils
from mathutils import Vector
from ...base_panel import BasePanel


class ZENU_OT_rotate_selected_uv(bpy.types.Operator):
    bl_label = 'Rotate UV'
    bl_idname = 'zenu.rotate_selected_uv'
    angle: bpy.props.FloatProperty(name='Angle', default=1.5708)

    def execute(self, context: bpy.types.Context):
        prev = bpy.context.space_data.pivot_point

        bpy.context.space_data.pivot_point = 'INDIVIDUAL_ORIGINS'

        bpy.ops.transform.rotate(value=self.angle, orient_axis='Z', orient_type='VIEW',
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        bpy.context.space_data.pivot_point = prev

        return {'FINISHED'}


class ZENU_OT_move_uv_by_pixel(bpy.types.Operator):
    bl_label = 'Move'
    bl_idname = 'zenu.move_by_pixel'
    bl_options = {'UNDO'}
    add: bpy.props.BoolProperty(default=True)
    step: bpy.props.StringProperty()

    def select_layout(self, context: bpy.types.Context, mesh_origin: bpy.types.Mesh):
        resolution = Vector((context.scene.zenu_uv_resolution_x, context.scene.zenu_uv_resolution_y))
        offset = Vector((context.scene.zenu_uv_offset_x / resolution.x, context.scene.zenu_uv_offset_x / resolution.y))

        move = Vector((0, 0, 0))

        if self.step == 'left':
            move.x = -offset.x
        if self.step == 'right':
            move.x = offset.x

        if self.step == 'up':
            move.y = offset.y
        if self.step == 'down':
            move.y = -offset.y

        if not self.add:
            move = -move

        bpy.ops.transform.translate(value=move, orient_type='GLOBAL',
                                    orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)))

    def execute(self, context: bpy.types.Context):
        for obj in context.selected_objects:
            self.select_layout(context, obj.data)

        return {'FINISHED'}


class ZENU_OT_select_uv_shell(bpy.types.Operator):
    bl_label = 'Select UV Shell'
    bl_idname = 'zenu.select_uv_shell'
    select_vertical: bpy.props.BoolProperty(name='Select Vertical', default=False)

    def select_layout(self, context: bpy.types.Context, mesh_origin: bpy.types.Mesh):
        mesh: bmesh.types.BMesh = bmesh.from_edit_mesh(mesh_origin)
        uv_layer: bmesh.types.BMLayerItem = mesh.loops.layers.uv.active
        islands = bmesh_utils.bmesh_linked_uv_islands(mesh, uv_layer)
        threshold: float = context.scene.zenu_uv_aspect_threshold

        # print(uv_layer)
        for island in islands:
            loops = []
            min_box = Vector((float('inf'), float('inf')))
            max_box = Vector((float('-inf'), float('-inf')))

            for face in island:
                face: bmesh.types.BMFace

                for loop in face.loops:
                    uv_loop: bmesh.types.BMLoopUV = loop[uv_layer]
                    uv: Vector = uv_loop.uv
                    loops.append(uv_loop)

                    if uv.x < min_box.x:
                        min_box.x = uv.x

                    if uv.y < min_box.y:
                        min_box.y = uv.y

                    if uv.x > max_box.x:
                        max_box.x = uv.x

                    if uv.y > max_box.y:
                        max_box.y = uv.y
            aspect_horizontal = (max_box.x - min_box.x) / (max_box.y - min_box.y)
            aspect_vertical = (max_box.y - min_box.y) / (max_box.x - min_box.x)

            if aspect_horizontal > threshold and not self.select_vertical:
                for i in loops:
                    i.select = True
            elif aspect_vertical > threshold and self.select_vertical:
                for i in loops:
                    i.select = True

        bmesh.update_edit_mesh(mesh_origin)

    def execute(self, context: bpy.types.Context):
        bpy.ops.uv.select_mode(type='VERTEX')
        # mesh = context.active_object.data

        for obj in context.selected_objects:
            self.select_layout(context, obj.data)

        return {'FINISHED'}


class ZENU_OT_select_uv_res(bpy.types.Operator):
    bl_label = 'Select UV Res'
    bl_idname = 'zenu.select_uv_res'
    x: bpy.props.IntProperty()
    y: bpy.props.IntProperty()

    def execute(self, context: bpy.types.Context):
        context.scene.zenu_uv_resolution_x = self.x
        context.scene.zenu_uv_resolution_y = self.y
        return {'FINISHED'}


class ZENU_PT_uv_utils(BasePanel):
    bl_label = 'UV Utils'
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        if bpy.context.scene.tool_settings.use_uv_select_sync:
            layout.prop(bpy.context.scene.tool_settings, 'use_uv_select_sync', text='Disable UV Sync')
            return

        col = layout.column(align=True)
        col.scale_y = 1.4
        col.prop(context.scene, 'zenu_uv_aspect_threshold')
        op = col.operator(ZENU_OT_select_uv_shell.bl_idname, text='Select Horizontal Islands')
        op.select_vertical = False
        op = col.operator(ZENU_OT_select_uv_shell.bl_idname, text='Select Vertical Islands')
        op.select_vertical = True

        row = col.row(align=True)
        op = row.operator(ZENU_OT_rotate_selected_uv.bl_idname, text='-90°')
        op.angle = -1.5708

        op = row.operator(ZENU_OT_rotate_selected_uv.bl_idname, text='90°')
        op.angle = 1.5708

        col = layout.column(align=True)
        col.scale_y = 1.4
        row = col.row(align=True)
        op = row.operator(ZENU_OT_select_uv_res.bl_idname, text='4K')
        op.x = 4096
        op.y = 4096
        op = row.operator(ZENU_OT_select_uv_res.bl_idname, text='2K')
        op.x = 2048
        op.y = 2048
        op = row.operator(ZENU_OT_select_uv_res.bl_idname, text='1K')
        op.x = 1024
        op.y = 1024

        col.prop(context.scene, 'zenu_uv_resolution_x')
        col.prop(context.scene, 'zenu_uv_resolution_y')
        col.prop(context.scene, 'zenu_uv_offset_x', text='Step')
        # col.prop(context.scene, 'zenu_uv_offset_y')

        # op = col.operator(ZENU_OT_move_uv_by_pixel.bl_idname, text='Add')
        # op.add = True
        # op = col.operator(ZENU_OT_move_uv_by_pixel.bl_idname, text='Subtract')
        # op.add = False

        move = layout.column(align=True)
        op = move.operator(ZENU_OT_move_uv_by_pixel.bl_idname, text='', icon='TRIA_UP')
        op.step = 'up'
        row = move.row(align=True)
        row.scale_x = 100
        op = row.operator(ZENU_OT_move_uv_by_pixel.bl_idname, text='', icon='TRIA_LEFT')
        op.step = 'left'
        op = row.operator(ZENU_OT_move_uv_by_pixel.bl_idname, text='', icon='TRIA_RIGHT')
        op.step = 'right'
        op = move.operator(ZENU_OT_move_uv_by_pixel.bl_idname, text='', icon='TRIA_DOWN')
        op.step = 'down'


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_uv_utils,
    ZENU_OT_select_uv_shell,
    ZENU_OT_rotate_selected_uv,
    ZENU_OT_move_uv_by_pixel,
    ZENU_OT_select_uv_res
))


def register():
    bpy.types.Scene.zenu_uv_resolution_x = bpy.props.IntProperty(
        name='Resolution X',
        default=1024,
        min=2,
        subtype='PIXEL'
    )
    bpy.types.Scene.zenu_uv_resolution_y = bpy.props.IntProperty(
        name='Resolution Y',
        default=1024,
        min=2,
        subtype='PIXEL'
    )
    bpy.types.Scene.zenu_uv_offset_x = bpy.props.IntProperty(
        name='Offset X',
        default=0,
        subtype='PIXEL'
    )
    bpy.types.Scene.zenu_uv_offset_y = bpy.props.IntProperty(
        name='Offset Y',
        default=0,
        subtype='PIXEL'
    )

    bpy.types.Scene.zenu_uv_aspect_threshold = bpy.props.FloatProperty(
        name='Threshold',
        default=1.1,
        min=1,
        soft_max=10,
        subtype='FACTOR'
    )
    reg()


def unregister():
    unreg()

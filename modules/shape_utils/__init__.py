import numpy as np

import bpy
from ...base_panel import BasePanel


class ShapeMirror(bpy.types.PropertyGroup):
    left_group: bpy.props.StringProperty()
    right_group: bpy.props.StringProperty()


class ZENU_OT_shape_mirror(bpy.types.Operator):
    bl_label = 'Create Shape Mirror'
    bl_idname = 'zenu.create_shape_mirror'
    bl_options = {"UNDO"}

    def get_or_create_shape(self, obj: bpy.types.Object, name: str) -> tuple[bpy.types.ShapeKey, bool]:
        shapes = obj.data.shape_keys.key_blocks
        shape = shapes.get(name)

        if shape:
            return shape, True

        prev = obj.show_only_shape_key
        obj.show_only_shape_key = True
        shape = obj.shape_key_add(name=name, from_mix=True)
        obj.show_only_shape_key = prev

        return shape, False

    def replace(self, _from: bpy.types.ShapeKey, to: bpy.types.ShapeKey):
        vertex_count = len(_from.data)

        data = np.zeros(vertex_count * 3, dtype=np.float32)
        _from.data.foreach_get('co', data.ravel())

        to.data.foreach_set('co', data)
        self.report({'INFO'}, f'Copy {_from.name} -> {to.name}')

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        shape = context.active_object.active_shape_key
        vertex_count = len(obj.data.vertices)

        shape_mirror = obj.shape_mirror
        left = shape_mirror.left_group
        right = shape_mirror.right_group

        prev = obj.show_only_shape_key
        obj.show_only_shape_key = True

        side = 'empty'
        shape_name = shape.name

        if '.' in shape_name:
            shape_name, side = shape.name.split('.')

        side: str = side.lower()

        shape_l, is_exists_l = self.get_or_create_shape(obj, shape_name + '.L')
        shape_r, is_exists_r = self.get_or_create_shape(obj, shape_name + '.R')

        obj.show_only_shape_key = prev

        shape_l.vertex_group = left
        shape_r.vertex_group = right

        if not is_exists_l and not is_exists_r:
            self.report({'INFO'}, f'Created {shape_l.name}, {shape_r.name}')

        if side == 'l':
            self.replace(shape_l, shape_r)
        elif side == 'r':
            self.replace(shape_r, shape_l)

        return {'FINISHED'}


class ZENU_PT_shape_mirror(BasePanel):
    bl_label = 'Shape Mirror'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        shape_mirror = context.active_object.shape_mirror
        obj = context.active_object

        lay = layout.box().column_flow(align=True)
        lay.label(text='Left/Right Group')

        lay.prop_search(shape_mirror, 'left_group', obj, 'vertex_groups', text='')
        lay.prop_search(shape_mirror, 'right_group', obj, 'vertex_groups', text='')

        layout.operator(ZENU_OT_shape_mirror.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_shape_mirror,
    ZENU_OT_shape_mirror,
    ShapeMirror
))


def register():
    reg()
    bpy.types.Object.shape_mirror = bpy.props.PointerProperty(type=ShapeMirror)


def unregister():
    unreg()

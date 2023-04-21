import math

import bpy
from bpy.types import Context
from ..base_panel import BasePanel
from ..utils import check_mods


class ZENU_OT_align(bpy.types.Operator):
    bl_label = 'Align'
    bl_idname = 'zenu.align'
    bl_options = {'REGISTER', 'UNDO'}
    coordinate: bpy.props.EnumProperty(items=(('x', 'X', ''), ('y', 'Y', ''), ('z', 'Z', '')))

    def execute(self, context: Context):
        cord = self.coordinate
        sort = context.scene.align_cord
        invert = False
        objects = []

        min_obj: bpy.types.Object = context.active_object
        max_obj: bpy.types.Object = context.active_object

        for obj in context.selected_objects:
            min_p = getattr(min_obj.location, sort)
            current = getattr(obj.location, sort)

            if min_p > current:
                min_obj = obj
            objects.append(obj)

        try:
            objects.remove(min_obj)
        except ValueError:
            pass
        try:
            objects.remove(max_obj)
        except ValueError:
            pass

        objects = sorted(objects, key=lambda i: getattr(i.location, sort))

        max_pos = getattr(max_obj.location, cord)
        min_pos = getattr(min_obj.location, cord)

        dist = math.dist((min_pos, 0), (max_pos, 0))

        length = dist / (len(objects) + 1)

        direction = min_pos - max_pos > 0
        if direction:
            pos = min_pos - length
        else:
            pos = min_pos + length

        for i, obj in enumerate(objects):
            setattr(obj.location, cord, pos)

            if direction:
                pos -= length
            else:
                pos += length

        return {'FINISHED'}


class ZENU_PT_align_tools(BasePanel):
    bl_label = 'Align Tools'
    bl_context = ''

    @classmethod
    def poll(cls, context: 'Context'):
        return check_mods('o')

    def draw(self, context: Context):
        col = self.layout.column_flow(align=True)
        col.prop(context.scene, 'align_cord', text='')

        row = col.row(align=True)

        ops = row.operator(ZENU_OT_align.bl_idname, text='X')
        ops.coordinate = 'x'

        ops = row.operator(ZENU_OT_align.bl_idname, text='Y')
        ops.coordinate = 'y'

        ops = row.operator(ZENU_OT_align.bl_idname, text='Z')
        ops.coordinate = 'z'


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_align_tools,
    ZENU_OT_align
))


def register():
    bpy.types.Scene.align_cord = bpy.props.EnumProperty(items=(
        ('x', 'X', ''),
        ('y', 'Y', ''),
        ('z', 'Z', '')))
    reg()


def unregister():
    unreg()

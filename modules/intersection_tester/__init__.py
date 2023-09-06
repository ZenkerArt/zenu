# TODO: Сделать быстрое создание лоу-поли для мема со скелетом
# TODO: Быстрое создание иерархий коллекций
import math

import bpy
from bpy.types import Context
from ...base_panel import BasePanel
import mathutils


def intersect(a, b):
    return (
            a.minX <= b.maxX and
            a.maxX >= b.minX and
            a.minY <= b.maxY and
            a.maxY >= b.minY and
            a.minZ <= b.maxZ and
            a.maxZ >= b.minZ
    )


class Bounding:
    maxX = -math.inf
    minX = math.inf
    maxY = -math.inf
    minY = math.inf
    maxZ = -math.inf
    minZ = math.inf


def to_normal_bounding_box(bounding) -> Bounding:
    bound = Bounding()

    for b in bounding:
        if bound.minX > b[0]:
            bound.minX = b[0]

        if bound.minY > b[1]:
            bound.minY = b[1]

        if bound.minZ > b[2]:
            bound.minZ = b[2]

        if bound.maxX < b[0]:
            bound.maxX = b[0]

        if bound.maxY < b[1]:
            bound.maxY = b[1]

        if bound.maxZ < b[2]:
            bound.maxZ = b[2]

    return bound


class ZENU_OT_test_intersection(bpy.types.Operator):
    bl_label = 'Test Intersection'
    bl_idname = 'zenu.test_intersection'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def execute(self, context: Context):
        bounding = [bpy.context.object.matrix_world @ mathutils.Vector(bbox_co[:]) for bbox_co in
                    bpy.context.object.bound_box[:]]
        test_bounding = to_normal_bounding_box(bounding)

        for i in bpy.data.objects:
            if i.name == context.object.name: continue
            bounding = [i.matrix_world @ mathutils.Vector(bbox_co[:]) for bbox_co in
                        i.bound_box[:]]

            if intersect(test_bounding, to_normal_bounding_box(bounding)):
                i.select_set(True)

        return {'FINISHED'}


class ZENU_PT_test_intersection(BasePanel):
    bl_label = 'Test Intersection'

    def draw(self, context: Context):
        layout = self.layout
        col = layout.split(align=True)
        col.operator(ZENU_OT_test_intersection.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_test_intersection,
    ZENU_PT_test_intersection
))


def register():
    reg()


def unregister():
    unreg()

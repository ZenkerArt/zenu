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


def get_object_bounding(obj: bpy.types.Object):
    bounding = [obj.matrix_world @ mathutils.Vector(bbox_co[:]) for bbox_co in
                obj.bound_box[:]]

    return to_normal_bounding_box(bounding)


class ZENU_OT_test_intersection(bpy.types.Operator):
    bl_label = 'Select from intersection'
    bl_idname = 'zenu.test_intersection'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def execute(self, context: Context):
        test_bounding = get_object_bounding(context.object)

        for i in bpy.data.objects:
            if i.name == context.object.name: continue

            if intersect(test_bounding, get_object_bounding(i)):
                i.select_set(True)

        return {'FINISHED'}


class ZENU_OT_test_intersection_all(bpy.types.Operator):
    bl_label = 'Test Intersection All'
    bl_idname = 'zenu.test_intersection_all'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def execute(self, context: Context):
        for i in bpy.data.objects:
            for j in bpy.data.objects:
                if j.name == i.name: continue

                if intersect(get_object_bounding(j), get_object_bounding(i)):
                    j.select_set(True)

        return {'FINISHED'}


class ZENU_OT_test_intersection_in_selection(bpy.types.Operator):
    bl_label = 'Test Intersection In Selection'
    bl_idname = 'zenu.test_intersection_in_selection'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def execute(self, context: Context):
        arr = []
        for i in context.selected_objects:
            for j in context.selected_objects:
                if j.name == i.name: continue

                if intersect(get_object_bounding(j), get_object_bounding(i)):
                    arr.append(j)

        bpy.ops.object.select_all(action='DESELECT')

        for obj in arr:
            obj.select_set(True)

        return {'FINISHED'}

class ZENU_PT_test_intersection(BasePanel):
    bl_label = 'Test Intersection'

    def draw(self, context: Context):
        layout = self.layout
        layout.operator(ZENU_OT_test_intersection.bl_idname)
        layout.operator(ZENU_OT_test_intersection_all.bl_idname)
        layout.operator(ZENU_OT_test_intersection_in_selection.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_test_intersection,
    ZENU_OT_test_intersection_all,
    ZENU_OT_test_intersection_in_selection,
    ZENU_PT_test_intersection
))


def register():
    reg()


def unregister():
    unreg()

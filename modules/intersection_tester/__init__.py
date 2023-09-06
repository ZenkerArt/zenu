# TODO: Сделать быстрое создание лоу-поли для мема со скелетом
# TODO: Быстрое создание иерархий коллекций
import math
from typing import List, Any

import numpy

import bpy
from bpy.types import Context
from ...base_panel import BasePanel
import mathutils

cash = {}


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
    __slots__ = ['maxX', 'minX', 'maxY', 'minY', 'maxZ', 'minZ']

    def __init__(self):
        self.maxX = -math.inf  # 0
        self.minX = math.inf  # 1
        self.maxY = -math.inf  # 2
        self.minY = math.inf  # 3
        self.maxZ = -math.inf  # 4
        self.minZ = math.inf  # 5


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


def get_object_bounding_same_bounds(obj: bpy.types.Object, bounds):
    global bounding__

    if cash.get(obj.name) is None:
        bounding = [obj.matrix_world @ mathutils.Vector(bbox_co[:]) for bbox_co in bounds]
        cash[obj.name] = to_normal_bounding_box(bounding)
    return cash[obj.name]


def get_object_bounding(obj: bpy.types.Object):
    if cash.get(obj.name) is None:
        bounding = [obj.matrix_world @ mathutils.Vector(bbox_co[:]) for bbox_co in obj.bound_box[:]]

        cash[obj.name] = to_normal_bounding_box(bounding)
    return cash[obj.name]


class ZENU_OT_test_intersection(bpy.types.Operator):
    bl_label = 'Select from intersection'
    bl_idname = 'zenu.test_intersection'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def execute(self, context: Context):
        cash.clear()
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
        cash.clear()
        bpy.ops.object.select_all(action='DESELECT')

        for i in bpy.data.objects:
            bounding = get_object_bounding(i)
            for j in bpy.data.objects:
                if j.name == i.name: continue

                if intersect(get_object_bounding(j), bounding):
                    j.select_set(True)

        return {'FINISHED'}


class ZENU_OT_test_intersection_all_same_bounds(bpy.types.Operator):
    bl_label = 'Test Intersection All Same Bounds Opt'
    bl_idname = 'zenu.test_intersection_all_same_bounds'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def execute(self, context: Context):
        cash.clear()
        bpy.ops.object.select_all(action='DESELECT')
        bound = context.object.bound_box

        for i in bpy.data.objects:
            bounding = get_object_bounding(i)
            for j in bpy.data.objects:
                if j.name == i.name: continue

                if intersect(get_object_bounding_same_bounds(j, bound), bounding):
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
        cash.clear()

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
        layout.operator(ZENU_OT_test_intersection_all_same_bounds.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_test_intersection,
    ZENU_OT_test_intersection_all,
    ZENU_OT_test_intersection_all_same_bounds,
    ZENU_OT_test_intersection_in_selection,
    ZENU_PT_test_intersection
))


def register():
    reg()


def unregister():
    unreg()

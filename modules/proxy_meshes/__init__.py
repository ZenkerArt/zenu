from dataclasses import dataclass

import bpy
import bmesh
from mathutils import Vector
from ...base_panel import BasePanel


@dataclass
class Vertex:
    pos: Vector
    normal: Vector
    name: str
    index: int


class ZENU_OT_create_bones(bpy.types.Operator):
    bl_label = 'Create Bones'
    bl_idname = 'zenu.create_bones'
    bl_options = {'REGISTER', 'UNDO'}

    def create_groups(self, obj: bpy.types.Object, verts: list[Vertex]):
        for i in verts:
            group = obj.vertex_groups.new(name=i.name)
            group.add((i.index,), 1, 'REPLACE')

    @staticmethod
    def select(obj: bpy.types.Object):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

    def add_bones(self, obj: bpy.types.Object, deformer_rest_obj: bpy.types.Object):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]

        verts: list[Vertex] = list()
        for index, i in enumerate(selected_verts):
            name = f'Vertex_{index}'
            verts.append(Vertex(
                pos=i.co,
                normal=i.normal,
                name=name,
                index=i.index
            ))

        bm.free()

        armature_data = bpy.data.armatures.new('Armature_Data')
        armature_obj = bpy.data.objects.new('Armature', armature_data)

        bpy.context.view_layer.layer_collection.collection.objects.link(armature_obj)
        bpy.ops.object.mode_set(mode='OBJECT')

        self.create_groups(obj, verts)
        self.create_groups(deformer_rest_obj, verts)
        "awda".endswith()
        bpy.ops.object.select_all(action='DESELECT')
        self.select(armature_obj)
        bpy.ops.object.mode_set(mode='EDIT')

        for vert in verts:
            bone = armature_data.edit_bones.new(vert.name)
            bone.head = vert.pos
            bone.tail = vert.pos + vert.normal * .1

        bpy.ops.object.mode_set(mode='POSE')
        for vert in verts:
            bone = armature_obj.pose.bones[vert.name]
            # child_of: bpy.types.ChildOfConstraint = bone.constraints.new(type='CHILD_OF')
            # child_of.target = deformer_rest_obj
            # child_of.subtarget = vert.name

            # child_of.

        mod = obj.modifiers.new('Deformer Bind', type='ARMATURE')
        mod.object = armature_obj

    def remove_armature_mod(self, obj: bpy.types.Object):
        for mod in obj.modifiers:
            if isinstance(mod, bpy.types.ArmatureModifier):
                obj.modifiers.remove(mod)

    def execute(self, context: bpy.types.Context):

        bpy.ops.object.mode_set(mode='OBJECT')

        target = context.active_object

        name = context.active_object.name

        bpy.ops.object.duplicate()
        context.active_object.name = f'{name}_Deformer'
        deformer_obj = context.active_object

        bpy.ops.object.duplicate()
        context.active_object.name = f'{name}_DeformerRest'
        deformer_rest_obj = context.active_object
        bpy.data.node_groups["ProxyDeformer"].name = "ProxyDeformer"

        node = bpy.data.node_groups["ProxyDeformer"]

        mod = target.modifiers.new('Proxy Deformer', type='NODES')
        mod.node_group = node

        deformer = node.interface.items_tree['Deformer'].identifier
        deformer_rest = node.interface.items_tree['Rest Deformer'].identifier

        mod[deformer] = deformer_obj
        mod[deformer_rest] = deformer_rest_obj

        self.add_bones(deformer_obj, deformer_rest_obj)
        # self.remove_armature_mod(deformer_obj)
        # self.remove_armature_mod(deformer_rest_obj)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = target
        target.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class ZENU_PT_proxy_meshes(BasePanel):
    bl_label = 'Proxy Meshes'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_create_bones.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_create_bones,
    ZENU_PT_proxy_meshes,
))


def register():
    reg()


def unregister():
    unreg()

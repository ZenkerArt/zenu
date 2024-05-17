import bpy
from ...utils import is_type
from ...base_panel import BasePanel


def insert_key(bone, keyframe_offset=0):
    # bpy.context.scene.keying_sets.active.type_info

    context = bpy.context

    bone.keyframe_insert('location', frame=context.scene.frame_current + keyframe_offset)
    bone.keyframe_insert('rotation_euler', frame=context.scene.frame_current + keyframe_offset)
    bone.keyframe_insert('rotation_quaternion', frame=context.scene.frame_current + keyframe_offset)
    bone.keyframe_insert('scale', frame=context.scene.frame_current + keyframe_offset)


def unparent(obj, bone, constraint):
    mat = obj.matrix_world @ bone.matrix

    constraint.influence = 1
    constraint.keyframe_insert('influence', frame=bpy.context.scene.frame_current - 1)
    insert_key(bone, -1)

    constraint.influence = 0
    constraint.keyframe_insert('influence')
    bone.matrix = mat
    insert_key(bone)


def parent(obj, bone, constraint):
    mat = obj.matrix_world @ bone.matrix

    constraint.influence = 0
    constraint.keyframe_insert('influence', frame=bpy.context.scene.frame_current - 1)
    insert_key(bone, -1)

    constraint.influence = 1
    constraint.keyframe_insert('influence')
    bone.matrix = mat
    insert_key(bone)


class ZENU_OT_child_of_unparent(bpy.types.Operator):
    bl_options = {'UNDO'}
    bl_label = 'Unparent'
    bl_idname = 'zenu.child_of_unparent'
    object_name: bpy.props.StringProperty('Object Name')
    bone_name: bpy.props.StringProperty('Bone Name')
    constraint_name: bpy.props.StringProperty('Constraint Name')

    def execute(self, context: bpy.types.Context):
        obj = context.scene.objects.get(self.object_name)

        if not is_type(obj, bpy.types.Armature):
            self.report({'WARNING'}, 'Object not found')
            return {'CANCELLED'}

        bone: bpy.types.PoseBone = obj.pose.bones[self.bone_name]
        constraint: bpy.types.ChildOfConstraint = bone.constraints[self.constraint_name]
        if constraint.influence > .5:
            unparent(obj, bone, constraint)
        else:
            self.report({'WARNING'}, 'Constraint unparented')
            return {'CANCELLED'}
        return {'FINISHED'}


class ZENU_PT_constraint_utils(BasePanel):
    bl_label = 'Constraint Utils'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        bone = context.active_pose_bone

        if bone is None:
            return

        for constraint in bone.constraints:
            if not isinstance(constraint, bpy.types.ChildOfConstraint):
                continue

            box = layout.box()
            box.label(text=constraint.name)
            op = box.operator(ZENU_OT_child_of_unparent.bl_idname)
            op.object_name = context.active_object.name
            op.bone_name = bone.name
            op.constraint_name = constraint.name


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_constraint_utils,
    ZENU_OT_child_of_unparent,
))


def register():
    reg()


def unregister():
    unreg()

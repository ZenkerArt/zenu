import bpy
from bpy.app.handlers import persistent
from .context import ov_context
from .rotation_based_overlapper import RotationBasedOverlapper
from .overlapper_settings import OverlapperSettings
from ...base_panel import BasePanel


def find_bone_chain(bone: bpy.types.PoseBone, bones: list[bpy.types.PoseBone] = None):
    if bones is None:
        bones = []

    if bone.child is None:
        bones.append(bone)
        return bones

    child_pos = bone.child.matrix.to_translation()
    pos = bone.matrix.to_translation() + bone.vector

    length = abs((child_pos - pos).length)

    bones.append(bone)
    if length < .01:
        bones.append(bone)
        return find_bone_chain(bone.child, bones)

    return bones


class ZENU_OT_overlapper(bpy.types.Operator):
    bl_label = 'Overlap'
    bl_idname = 'zenu.overlapper'

    def execute(self, context: bpy.types.Context):
        r = RotationBasedOverlapper(ov_context.baker, ov_context.settings)
        r.calc()
        ov_context.constraints.create_constraints()
        return {'FINISHED'}


class ZENU_OT_bake_transforms(bpy.types.Operator):
    bl_label = 'Bake Transforms'
    bl_idname = 'zenu.bake_transforms'

    def execute(self, context: bpy.types.Context):
        ov_context.constraints.remove_constraints()
        ov_context.baker.clear()
        ov_context.visual.clear()

        bones = sorted(context.selected_pose_bones,
                       key=lambda bone: bone.ov_settings.index)

        parent = None

        for index, bone in enumerate(bones):
            if bone.ov_settings.index == -1:
                bone.ov_settings.index = index

            tmp = ov_context.baker.add_bone(
                context.active_object, bone, parent
            )
            tmp.index = index
            if parent is not None:
                parent.child = tmp

            parent = tmp

        first = ov_context.baker.get_bone_records()[0][1]
        first.parent = first

        length = len(ov_context.baker.get_bone_records()) - 1
        last = ov_context.baker.get_bone_records()[length][1]
        last.child = last

        offset = ov_context.settings.bake_offset

        start, end = context.scene.frame_start, context.scene.frame_end

        if bpy.context.scene.use_preview_range:
            start, end = context.scene.frame_preview_start, context.scene.frame_preview_end

        ov_context.baker.bake(start, end, offset)
        return {'FINISHED'}


class ZENU_OT_overlapper_constraint(bpy.types.Operator):
    bl_label = 'Overlapper Constraint'
    bl_idname = 'zenu.overlapper_constraint'
    bl_options = {'UNDO'}
    action: bpy.props.EnumProperty(items=(
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
        ('BAKE_ACTION', 'Bake Action', ''),
    ))

    def execute(self, context: bpy.types.Context):
        if self.action == 'ADD':
            ov_context.constraints.create_constraints()
        elif self.action == 'REMOVE':
            ov_context.constraints.remove_constraints()
        elif self.action == 'BAKE_ACTION':
            name = context.active_object.name
            
            prev_action = context.active_object.animation_data.action
            action_name = f'{name}_overlapper'
            
            action = bpy.data.actions.get(action_name)
            
            if action is None:
                action = prev_action.copy()
                action.name = action_name
                
                # action.
                # action = bpy.data.actions.new(action_name)
            
            context.active_object.animation_data.action_blend_type = 'COMBINE'
            context.active_object.animation_data.action = action
            bpy.ops.nla.bake(frame_start=ov_context.baker.start,
                             frame_end=ov_context.baker.end,
                             visual_keying=True,
                             clear_constraints=True,
                             use_current_action=True,
                             bake_types={'POSE'})
            context.active_object.animation_data.action = prev_action
            # ov_context.baker.start_offset
            # context.selected_pose_bones
        return {'FINISHED'}


class ZENU_PT_overlapper(BasePanel):
    bl_label = 'Overlapper'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        settings: OverlapperSettings = context.scene.ov_settings

        layout = self.layout

        layout.operator(ZENU_OT_overlapper.bl_idname)
        layout.operator(ZENU_OT_bake_transforms.bl_idname)

        col = layout.column(align=True)
        op = col.operator(ZENU_OT_overlapper_constraint.bl_idname,
                          text='Add Constraints')
        op.action = 'ADD'

        op = col.operator(ZENU_OT_overlapper_constraint.bl_idname,
                          text='Remove Constraints')
        op.action = 'REMOVE'

        op = col.operator(ZENU_OT_overlapper_constraint.bl_idname,
                          text='Bake Action')
        op.action = 'BAKE_ACTION'

        col = layout.column(align=True)
        col.scale_y = 1.5
        col.scale_x = 1.5
        col.prop(settings, 'stiffness')
        col.prop(settings, 'damping')

        row = col.row(align=True)
        row.prop(settings, 'only_root_motion', icon='BONE_DATA', text='')
        row.prop(settings, 'motion_multiply')

        col.prop(settings, 'bake_offset')

        col = layout.row(align=True)
        col.scale_y = 1.5
        col.scale_x = 1.5
        col.prop(settings, 'wind', text='')

        if context.active_pose_bone:
            bone_settings: OverlapperBone = context.active_pose_bone.ov_settings
            layout.prop(bone_settings, 'index')


class OverlapperBone(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(default=-1)


@persistent
def loop(dummy):

    if not ov_context.baker.is_bake:
        return


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_overlapper,
    ZENU_OT_overlapper,
    ZENU_OT_bake_transforms,
    ZENU_OT_overlapper_constraint,
    OverlapperSettings,
    OverlapperBone
))


def register():
    reg()
    bpy.app.handlers.frame_change_post.append(loop)
    ov_context.visual.register()

    bpy.types.Scene.ov_settings = bpy.props.PointerProperty(
        type=OverlapperSettings)
    bpy.types.PoseBone.ov_settings = bpy.props.PointerProperty(
        type=OverlapperBone)


def unregister():
    unreg()
    bpy.app.handlers.frame_change_post.remove(loop)
    ov_context.visual.unregister()

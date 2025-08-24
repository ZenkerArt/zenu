import bpy
from bpy.app.handlers import persistent
from .rotation_based_overlapper import RotationBasedOverlapper
from .overlapper_settings import OverlapperSettings
from .particle_system import ParticleSystem
from mathutils import Matrix, Vector
from .angular_solver import ZAngularSolver
from .transform_baker import TransformBaker
from .visual import OvVisualizer
from ...base_panel import BasePanel


def add_empty(name: str):
    empty = bpy.data.objects.get(name)

    if empty:
        return empty

    empty = bpy.data.objects.new(name, None)
    bpy.context.view_layer.layer_collection.collection.objects.link(empty)

    return empty


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


class ConstraintCreator:
    _baker: TransformBaker
    CONST_NAME = '[Zenu] Overlapper'

    def __init__(self, baker: TransformBaker):
        self._baker = baker

    def create_constraints(self):
        baker = self._baker

        for _, bone_rec in baker.get_bone_records():
            empty = add_empty(
                f'{bone_rec.raw.armature_name}_{bone_rec.raw.bone_name}'
            )
            length = bone_rec.raw.bone.length
            empty.scale = Vector((length, length, length))

            bone_rec.raw.damped_track_to(self.CONST_NAME, empty)

            for frame in baker.get_range():
                empty.matrix_world = bone_rec\
                    .get_frame(frame)\
                    .matrix_result @ Matrix.Scale(length, 4)
                empty.keyframe_insert(data_path='location', frame=frame)
                empty.keyframe_insert(data_path='rotation_euler', frame=frame)

    def remove_constraints(self):
        for bone in bpy.context.selected_pose_bones:
            empty = bpy.data.objects.get(
                f'{bpy.context.active_object.name}_{bone.name}'
            )
            const: bpy.types.DampedTrackConstraint = bone.constraints.get(
                self.CONST_NAME)

            if empty is not None:
                bpy.data.objects.remove(empty)

            if const is not None:
                bone.constraints.remove(const)


class OvContext:
    visual: OvVisualizer
    baker: TransformBaker
    angular_solver: ZAngularSolver
    ps: ParticleSystem

    def __init__(self):
        self.visual = OvVisualizer()
        self.baker = TransformBaker()
        self.constraints = ConstraintCreator(self.baker)
        self.angular_solver = ZAngularSolver()
        self.ps = ParticleSystem()

    @property
    def settings(self) -> 'OverlapperSettings':
        return bpy.context.scene.ov_settings


ov_context = OvContext()


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
                context.active_object, bone, parent)

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
    ))

    def execute(self, context: bpy.types.Context):
        if self.action == 'ADD':
            ov_context.constraints.create_constraints()
        elif self.action == 'REMOVE':
            ov_context.constraints.remove_constraints()
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

    # frame = bpy.context.scene.frame_current
    # v = ov_context.baker.get_iter()[0][1]
    # first_bone = v.get_frame(frame)

    # for name, value in ov_context.baker.get_iter():
    #     bone = value.get_frame(frame)

    #     # bone.matrix_result = bone.matrix_world

    #     point_result = ov_context.visual.get_xyz_point(name)
    #     point_result.scale = value.bone.bone.length
    #     point_result.transforms.local.matrix = bone.matrix_result


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

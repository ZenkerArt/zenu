from typing import Any
import bpy
from ..layers import BoneCollectorLayer, RigComponentsLayer
from ..rig_lib import RigComponent, RigContext



class ActionControl(RigComponent):
    name = 'Action Control'
    subtype: bpy.props.EnumProperty(items=[
        ('1D', '1D', ''),
        ('RADIUS', 'Radius', ''),
    ])
    d1_min: bpy.props.FloatProperty(
        subtype='DISTANCE', default=-.01, soft_min=-1, soft_max=1, step=.005)
    d1_max: bpy.props.FloatProperty(
        subtype='DISTANCE', default=.01, soft_min=-1, soft_max=1, step=.005)
    d2_distance: bpy.props.FloatProperty(
        subtype='DISTANCE', default=.01, soft_min=-1, soft_max=1, step=.005)
    create_constraint: bpy.props.BoolProperty(
        default=True, name='Create Bone Constraint', description='Create Bone Constraint')
    invert: bpy.props.BoolProperty(
        default=False, name='Invert', description='Invert Action Time')

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_property(dist: float, value: float):
        min_y, max_y = -dist, dist

        val = max(value, 0) / (max_y * 2)
        val -= min(value, 0) / (min_y * 2)
        val = .5 + val

        return val

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        layout.prop(data, cls.get_prop_name('subtype'), text='')
        subtype = getattr(data, cls.get_prop_name('subtype'))

        row = layout.row(align=True)
        if subtype == '1D':
            row.prop(data, cls.get_prop_name('d1_min'), text='')
            row.prop(data, cls.get_prop_name('d1_max'), text='')

        if subtype == 'RADIUS':
            row.prop(data, cls.get_prop_name('d2_distance'), text='')

        row.prop(data, cls.get_prop_name('create_constraint'),
                 text='', icon='CONSTRAINT_BONE')
        layout.prop(data, cls.get_prop_name('invert'), icon='ALIGN_BOTTOM')

        min_y, max_y = getattr(data, cls.get_prop_name('d1_min')), getattr(
            data, cls.get_prop_name('d1_max'))

        loc_y = context.active_pose_bone.location.y
        val = max(loc_y, 0) / (max_y * 2)
        val -= min(loc_y, 0) / (min_y * 2)
        val = .5 + val

        x = cls.create_property(getattr(data, cls.get_prop_name(
            'd2_distance')), context.active_pose_bone.location.x)
        y = cls.create_property(getattr(data, cls.get_prop_name(
            'd2_distance')), context.active_pose_bone.location.y)

        if subtype == '1D':
            layout.label(text=f'{val:.2}')
            
        if subtype == 'RADIUS':
            layout.label(text=f'x:{x:.2},{y:.2}')

    @classmethod
    def get_1d_range(cls, bone) -> tuple[float, float]:
        return ActionControl.get_prop_value(bone, 'd1_min'), ActionControl.get_prop_value(
            bone, 'd1_max')

    @classmethod
    def get_radius_range(cls, bone) -> tuple[float, float]:
        return -ActionControl.get_prop_value(bone, 'd2_distance'), ActionControl.get_prop_value(
            bone, 'd2_distance')

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, layers: RigComponentsLayer):
        pass
        # for bone in bones_collector.get_edit_bones_by_type(self):
        # bone..rotation_mode = 'XYZ'

    def execute_pose(self, context: RigContext, bones_collector: BoneCollectorLayer):
        for bone in bones_collector.get_rig_bones_by_type(self):
            bone = bone.pose
            bone.rotation_mode = 'XYZ'
            subtype: str = self.get_prop_value(bone, 'subtype')

            bone.lock_scale = [True, True, True]
            bone.lock_rotation = [True, True, True]

            if not self.get_prop_value(bone, 'create_constraint'):
                continue

            if subtype == '1D':
                bone.lock_location = [True, False, True]
                constraint: bpy.types.LimitLocationConstraint = bone.constraints.new(
                    'LIMIT_LOCATION')
                constraint.use_min_y = True
                constraint.use_max_y = True
                constraint.owner_space = 'LOCAL'
                constraint.use_transform_limit = True

                constraint.min_y = self.get_prop_value(bone, 'd1_min')
                constraint.max_y = self.get_prop_value(bone, 'd1_max')

            if subtype == 'RADIUS':
                bone.lock_location = [False, False, True]
                constraint: bpy.types.LimitLocationConstraint = bone.constraints.new(
                    'LIMIT_LOCATION')

                constraint.use_min_y = True
                constraint.use_max_y = True
                constraint.use_min_x = True
                constraint.use_max_x = True
                constraint.owner_space = 'LOCAL'
                constraint.use_transform_limit = True

                fmin, fmax = self.get_radius_range(bone)

                constraint.min_x = fmin
                constraint.max_x = fmax
                constraint.min_y = fmin
                constraint.max_y = fmax

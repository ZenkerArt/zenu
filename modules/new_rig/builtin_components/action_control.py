from typing import Any
import bpy
from ..layers import BoneCollectorLayer, RigComponentsLayer
from ..rig_lib import RigComponent, RigContext


class ActionControl(RigComponent):
    name = 'Action Control'
    subtype: bpy.props.EnumProperty(items=[
        ('1D', '1D', ''),
    ])
    d1_min: bpy.props.FloatProperty(
        subtype='DISTANCE', default=-.01, soft_min=-1, soft_max=1, step=.005)
    d1_max: bpy.props.FloatProperty(
        subtype='DISTANCE', default=.01, soft_min=-1, soft_max=1, step=.005)
    create_constraint: bpy.props.BoolProperty(default=True, name='Create Bone Constraint', description='Create Bone Constraint')
    invert: bpy.props.BoolProperty(default=False, name='Invert', description='Invert Action Time')

    def __init__(self):
        super().__init__()

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        layout.prop(data, cls.get_prop_name('subtype'), text='')

        row = layout.row(align=True)
        row.prop(data, cls.get_prop_name('d1_min'), text='')
        row.prop(data, cls.get_prop_name('d1_max'), text='')
        row.prop(data, cls.get_prop_name('create_constraint'), text='', icon='CONSTRAINT_BONE')
        layout.prop(data, cls.get_prop_name('invert'), icon='ALIGN_BOTTOM')

        min_y, max_y = getattr(data, cls.get_prop_name('d1_min')), getattr(
            data, cls.get_prop_name('d1_max'))

        loc_y = context.active_pose_bone.location.y
        val = max(loc_y, 0) / (max_y * 2)
        val -= min(loc_y, 0) / (min_y * 2)
        val = .5 + val
        
        layout.label(text=f'{round(val, 2)} {loc_y}')

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, layers: RigComponentsLayer):
        pass
        # for bone in bones_collector.get_edit_bones_by_type(self):
        # bone..rotation_mode = 'XYZ'

    def execute_pose(self, context: RigContext, bones_collector: BoneCollectorLayer):
        for bone in bones_collector.get_rig_bones_by_type(self):
            bone = bone.pose
            bone.rotation_mode = 'XYZ'
            bone.lock_scale = [True, True, True]
            bone.lock_location = [True, False, True]
            bone.lock_rotation = [True, True, True]

            if self.get_prop_value(bone, 'create_constraint'):
                constraint: bpy.types.LimitLocationConstraint = bone.constraints.new(
                    'LIMIT_LOCATION')
                constraint.use_min_y = True
                constraint.use_max_y = True
                constraint.owner_space = 'LOCAL'
                constraint.use_transform_limit = True

                constraint.min_y = self.get_prop_value(bone, 'd1_min')
                constraint.max_y = self.get_prop_value(bone, 'd1_max')

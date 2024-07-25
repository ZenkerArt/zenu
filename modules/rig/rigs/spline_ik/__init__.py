import math
from math import sin, pi

import bpy
from bpy.app.handlers import persistent
from .curve_control import CurveControl
from .curve_generator import CurveGenerator
from .point_control import PointControl
from ..rig_module import RigModule
from ...meta_bone import MetaBoneData


class SplineIKRig(RigModule):
    rig_name = 'Spline IK'

    auto_detect: bpy.props.BoolProperty(name='Auto Detect', default=True)
    chain_length: bpy.props.IntProperty(name='Chain Length', min=2, default=2, soft_max=100, subtype='FACTOR')

    spline_point_count: bpy.props.IntProperty(name='Point Count', min=2, default=3, soft_max=10, subtype='FACTOR')
    root_bone: bpy.props.StringProperty(name='Root Bone')

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        props = self.props

        box = layout.box().column(align=True)
        box.label(text='Spline')
        box.prop(props, self.get_prop_name('spline_point_count'))

        box = layout.box().column(align=True)
        box.label(text='Chain Length')
        box.prop(props, self.get_prop_name('auto_detect'))
        if not self.auto_detect:
            box.prop(props, self.get_prop_name('chain_length'))

        col = layout.column(align=True)
        col.label(text='Root Bone')
        col.prop_search(props, self.get_prop_name('root_bone'), self.bone.arm, 'bones', text='')

    def get_bones(self, bone: MetaBoneData):
        for index, bone in enumerate(bone.parent_list):
            if bone.parent is None:
                yield bone
                break

            if not self.auto_detect:
                if index > self.chain_length - 3:
                    yield bone
                    break
                continue

            if (bone.global_loc - bone.parent.global_loc_tail).length > .01:
                yield bone
                break
            yield bone

    def apply_spline_ik(self, chain_length: int, spline: bpy.types.Object):
        spline_constraint: bpy.types.SplineIKConstraint = None
        for i in self.bone.pose_bone.constraints:
            if i.type == 'SPLINE_IK':
                spline_constraint = i

        if spline_constraint is None:
            spline_constraint = self.bone.pose_bone.constraints.new('SPLINE_IK')

        spline_constraint.target = spline
        spline_constraint.chain_count = chain_length + 1
        spline_constraint.y_scale_mode = 'NONE'
        spline_constraint.xz_scale_mode = 'BONE_ORIGINAL'

    def execute_pose(self, context: bpy.types.Context):
        bones = list(self.get_bones(self.bone))

        st = CurveGenerator(self.bone, bones)
        spline = st.generate_spline(self.spline_point_count)
        self.add_dep(spline)
        self.apply_spline_ik(len(bones), spline)

        spline_gen = CurveControl(self.bone.obj, spline)
        spline_gen.create_controls(self.root_bone)

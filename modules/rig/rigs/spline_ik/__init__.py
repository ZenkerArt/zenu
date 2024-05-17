import math
from math import sin, pi

import bpy
from bpy.app.handlers import persistent
from .curve_control import CurveControl
from .curve_generator import CurveGenerator
from .point_control import PointControl
from ..rig_module import RigModule
from ...meta_bone import MetaBoneData


def tentacle_func(pos: float, time: float, radius: float, strength: float, thickness: float):
    try:
        accuracy = 10000
        count = radius * accuracy
        pos_t = pos + time

        dist = (((pos_t * accuracy) % count) / count)

        dist = thickness + (sin(dist * math.pi) / 2) * strength
    except Exception:
        return 0
    # print(dist)

    return 1


@persistent
def load_handler(dummy):
    bpy.app.driver_namespace['tentacle_func'] = tentacle_func


class SplineIKRig(RigModule):
    rig_name = 'Spline IK'

    auto_detect: bpy.props.BoolProperty(name='Auto Detect', default=True)
    chain_length: bpy.props.IntProperty(name='Chain Length', min=2, default=2, soft_max=100, subtype='FACTOR')

    spline_point_count: bpy.props.IntProperty(name='Point Count', min=2, default=3, soft_max=10, subtype='FACTOR')
    root_bone: bpy.props.StringProperty(name='Root Bone')

    def register(self) -> tuple:
        load_handler(None)
        bpy.app.handlers.load_post.append(load_handler)
        return tuple()

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

    def create_property(self, name: str, value: float = 0.0, min: float = 0, max: float = 1):
        arm = self.bone.obj

        name = f'zenu_{name}'
        arm[name] = value
        test = arm.id_properties_ui(name)
        test.update(min=min, max=max, default=value, subtype='FACTOR')
        return name

    def _driver_setup(self, bones: list[MetaBoneData]):
        bpy.ops.object.mode_set(mode='EDIT')

        self.bone.edit_bone.inherit_scale = 'NONE'
        for i in bones:
            i.edit_bone.inherit_scale = 'NONE'

        time_name = self.create_property('time')
        radius_name = self.create_property('radius')
        strength_name = self.create_property('strength', max=10)
        thickness_name = self.create_property('thickness', max=10)

        bpy.ops.object.mode_set(mode='POSE')
        bones_count = len(bones)
        arm = self.bone.obj

        def create_driver(bone: MetaBoneData, index: int) -> bpy.types.Driver:
            driver1 = bone.pose_bone.driver_add('scale', index).driver

            def prop(var_name: str, prop_name: str):
                var = driver1.variables.new()
                var.type = 'SINGLE_PROP'
                var.name = var_name
                tar = var.targets[0]
                tar.id = arm
                tar.data_path = f'["{prop_name}"]'

            prop('time', time_name)
            prop('radius', radius_name)
            prop('strength', strength_name)
            prop('thickness', thickness_name)

            return driver1

        for i, bone in enumerate(bones):
            driver1 = create_driver(bone, 0)
            driver2 = create_driver(bone, 2)

            exp = f'tentacle_func({i / bones_count}, time, radius, strength, thickness)'

            driver1.expression = exp
            driver2.expression = exp

    def execute(self, context: bpy.types.Context):
        bones = list(self.get_bones(self.bone))
        # self._driver_setup(bones)

        st = CurveGenerator(self.bone, bones)
        spline = st.generate_spline(self.spline_point_count)
        self.add_dep(spline)
        self.apply_spline_ik(len(bones), spline)

        spline_gen = CurveControl(self.bone.obj, spline)
        spline_gen.create_controls(self.root_bone)

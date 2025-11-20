from dataclasses import dataclass
from typing import Any
import bpy
from ..layers import BoneCollectorLayer, StyleLayer, BoneCollectionLayer
from ..rig_lib import RigBone, RigComponent, RigContext
from ..rig_lib.bone_utils import bone_create_lerp, clear_bone_collection


@dataclass
class PoseData:
    bbone_targets: list[RigBone]
    bone_originals: list[RigBone]
    bone_stretches: list[RigBone]


class BendyBone(RigComponent):
    name = 'Bendy Bone'
    pose_data: list[PoseData]

    def __init__(self):
        super().__init__()
        self.pose_data = []

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        pass

    def bone_prepare(self, bone: RigBone):
        # print(bone)
        bbone_targets: list[bpy.types.EditBone] = []
        bone_originals: list[bpy.types.EditBone] = []
        bone_stretches: list[bpy.types.EditBone] = []

        bone_edit = bone.edit
        bone_originals.append(bone_edit)
        bone_originals.extend(bone_edit.children_recursive)

        def create_bone(bone, factor: float, prefix: str):
            bb = bone_create_lerp(bone, factor, prefix=prefix)
            bb.bbone_x = bone.bbone_x * 2
            bb.bbone_z = bone.bbone_z * 2
            bb.length = bb.length / 10
            bb.use_deform = False
            return bb

        for index, original_bone in enumerate(bone_originals):
            if index == 0:
                bbone_target = create_bone(original_bone, 0, 'BBONE-TGT-')
                bbone_targets.append(bbone_target)

                bbone_stretch = create_bone(original_bone, 0, 'STR-')
                bone_stretches.append(bbone_stretch)

                bbone_target.parent = bbone_stretch

            bbone_target = create_bone(original_bone, 1, 'BBONE-TGT-')
            bbone_targets.append(bbone_target)

            bbone_stretch = create_bone(original_bone, 1, 'STR-')
            bone_stretches.append(bbone_stretch)

            bbone_target.parent = bbone_stretch

        for index, boned in enumerate(bone_originals):
            boned.use_connect = False
            boned.bbone_segments = 10

            boned.bbone_custom_handle_end = bbone_targets[index + 1]
            boned.bbone_handle_type_end = 'TANGENT'

            boned.bbone_custom_handle_start = bbone_targets[index]
            boned.bbone_handle_type_start = 'TANGENT'

            boned.parent = bone_stretches[index]
            boned.use_deform = True

        return bbone_targets, bone_originals, bone_stretches

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, style: StyleLayer, coll_ls: BoneCollectionLayer):
        for i in bones_collector.get_rig_bones_by_type(self):
            root_bone = i.edit
            root_bone.use_deform = False
            parent = root_bone.parent
            bbone_targets, bone_originals, bone_stretches = self.bone_prepare(
                i)

            pose_data = PoseData(
                bbone_targets=self.convert_bone(bbone_targets).results,
                bone_originals=self.convert_bone(bone_originals).results,
                bone_stretches=self.convert_bone(bone_stretches).results
            )

            self.pose_data.append(pose_data)

            coll = coll_ls.add_parent_collection(i, postfix=' Stretch')

            for target in pose_data.bbone_targets:
                coll_ls.add_to_mechanic(target)

            for stretch in pose_data.bone_stretches:
                clear_bone_collection(stretch.edit)
                coll.assign(stretch.edit)

                stretch.edit.parent = parent
                style.apply_shape(stretch, i.props.shape)

            for original in pose_data.bone_originals:
                coll_ls.add_to_deform(original)

    def execute_pose(self):
        for p in self.pose_data:
            for index, bone_original in enumerate(p.bone_originals):
                st = p.bone_stretches[index + 1]

                stretch_to: bpy.types.StretchToConstraint = bone_original.pose.constraints.new(
                    'STRETCH_TO')

                stretch_to.target = st.arm
                stretch_to.subtarget = st.name

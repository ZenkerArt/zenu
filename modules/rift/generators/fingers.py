import math

from ..rig_generator import RigGenerator
import bpy


class GeneratorFingers(RigGenerator):
    def execute(self, context: bpy.types.Context):
        self.start_edit()

        for side in ['L', 'R']:
            for finger in ['Little', 'Ring', 'Middle', 'Index', 'Thumb']:
                bone = self.get_edit_bone(f'cf_J_Hand_{finger}01_{side}')
                ctr = self.dup_bone('CTR_', bone.name)
                org = self.dup_bone('CTR_F_', bone.name)
                self.dup_bone('MCH_SCALE_', bone.name)
                self.apply_widget(ctr, 'WGT-FingerRotation')
                ed = self.get_edit_bone(ctr)
                ed.tail = self.get_edit_bone(f'cf_J_Hand_{finger}03_{side}').head
                ed.roll = 0

                self.get_edit_bone(org).parent = ed
                self.get_edit_bone(ctr).parent = bone.parent
                self.add_to_collection(org, f'Fingers/Fingers {side}')
                self.add_to_collection(ctr, f'Fingers/Fingers {side}')

        self.end_edit()
        obj = self.get_obj()

        for side in ['L', 'R']:
            for finger in ['Little', 'Ring', 'Middle', 'Index', 'Thumb']:
                for index in range(1, 4):
                    # bone = self.get_edit_bone()
                    # ctr = self.dup_bone('CTR_', bone.name)
                    bone_name = f'cf_J_Hand_{finger}0{index}_{side}'
                    ed = self.get_pose_bone(bone_name)

                    # transform: bpy.types.CopyTransformsConstraint = ed.constraints.new('COPY_TRANSFORMS')
                    if index == 1:
                        rotation: bpy.types.CopyRotationConstraint = ed.constraints.new('COPY_ROTATION')
                        rotation.target = obj
                        rotation.subtarget = f'CTR_F_{bone_name}'

                        org = self.get_pose_bone(f'CTR_F_{bone_name}')
                        scale: bpy.types.CopyRotationConstraint = org.constraints.new('COPY_SCALE')
                        scale.target = obj
                        scale.subtarget = f'MCH_SCALE_{bone_name}'

                        self.apply_widget(f'CTR_F_{bone_name}', 'WGT-Finger')
                        continue

                    transform: bpy.types.TransformConstraint = ed.constraints.new('TRANSFORM')
                    transform.target = obj
                    transform.subtarget = f'CTR_F_cf_J_Hand_{finger}01_{side}'
                    transform.target_space = 'LOCAL'
                    transform.owner_space = 'LOCAL'
                    transform.map_from = 'SCALE'
                    transform.map_to = 'ROTATION'

                    transform.from_min_y_scale = 0
                    transform.to_min_z_rot = -math.pi if side == 'R' else math.pi
                    transform.map_to_z_from = 'Y'
                    transform.map_to_y_from = 'Y'
                    transform.use_motion_extrapolate = True
                    transform.mix_mode_rot = 'ADD'

                    if finger == 'Thumb':
                        transform.to_min_z_rot = 0
                        transform.to_min_y_rot = math.pi if side == 'R' else -math.pi

        self.apply_all()
        return {'FINISHED'}

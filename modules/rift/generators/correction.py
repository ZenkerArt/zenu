import math

from ..rig_generator import RigGenerator
import bpy


class GeneratorCorrection(RigGenerator):
    bl_label = 'Create Correction'
    bl_idname = 'zenu.create_correction'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        copy_rotation: tuple[tuple[str, str, float], ...] = (
            ('cf_J_LegLow01_$DIR', 'cf_J_LegKnee_back_$DIR', 1),
            ('cf_J_LegLow01_$DIR', 'cf_J_LegKnee_dam_$DIR', .5),
            ('cf_J_LegUp00_$DIR', 'cf_J_LegUpDam_$DIR', .8),
            ('cf_J_ArmLow01_$DIR', 'cf_J_ArmElboura_dam_$DIR', .75),
            ('cf_J_ArmLow01_$DIR', 'cf_J_ArmElbo_dam_01_$DIR', .75),
        )

        for side in ['L', 'R']:
            for from_, to, inf in copy_rotation:
                self.create_copy_rotation(from_.replace('$DIR', side), to.replace('$DIR', side), inf)

            duplicated_bones = self.duplicate_bones('CORRECTIVE_', [
                f'cf_J_ArmLow01_{side}',
                f'cf_J_ArmLow02_dam_{side}',
                f'cf_J_Hand_Wrist_dam_{side}',
            ])
            self.create_copy_rotation(f'cf_J_Hand_s_{side}', duplicated_bones[0], 1)
            self.create_dumped_track(duplicated_bones[0], f'cf_J_Hand_s_{side}',
                                     'TRACK_X' if side == 'L' else 'TRACK_NEGATIVE_X')

            self.create_copy_transform(duplicated_bones[1], f'cf_J_ArmLow02_dam_{side}', 0.25)
            self.create_copy_transform(duplicated_bones[2], f'cf_J_Hand_Wrist_dam_{side}', 0.80)

        for side in ['L', 'R']:
            self.start_edit()

            obj = self.get_obj()
            arm: bpy.types.Armature = obj.data
            edit_bs = arm.edit_bones

            foot = f'cf_J_Foot01_{side}'
            leg_low_01 = f'cf_J_LegLow01_{side}'
            foot_inverse = self.dup_bone('CORRECTIVE_invers_', foot, parent=foot)
            bb = self.get_edit_bone(foot_inverse)
            bb.length = bb.length * -1
            bb.roll = math.pi

            leg_roll_name = f'CORRECTIVE_LegRoll_{side}'
            leg_roll: bpy.types.EditBone = edit_bs.new(leg_roll_name)
            leg_roll.head = self.get_edit_bone(leg_low_01).head
            leg_roll.tail = self.get_edit_bone(foot).head
            leg_roll.parent = self.get_edit_bone(leg_low_01)

            leg_roll_core_1 = self.dup_bone('CORRECTIVE_', f'cf_J_LegLow03_{side}', parent=leg_roll_name)
            leg_roll_core_2 = self.dup_bone('CORRECTIVE_', f'cf_J_LegLow02_s_{side}', parent=leg_roll_name)

            self.end_edit()

            self.create_copy_transform(leg_roll_core_1, f'cf_J_LegLow03_{side}', 0.5)
            self.create_copy_transform(leg_roll_core_2, f'cf_J_LegLow02_s_{side}', 0.5)
            self.create_copy_rotation(foot_inverse, leg_roll_name, 1)
            self.create_dumped_track(leg_roll_name, foot_inverse, 'TRACK_Y')

            const = self.create_copy_rotation(f'cf_J_ArmUp00_{side}', f'cf_J_ArmUp01_dam_{side}', .5)
            const.owner_space = 'LOCAL'
            const.target_space = 'LOCAL'
            const.invert_x = True
            const.use_y = False
            const.use_z = False

            const = self.create_copy_rotation(f'cf_J_LegUp00_{side}', f'cf_J_LegUp01_{side}', .5)
            const.owner_space = 'LOCAL'
            const.target_space = 'LOCAL'
            const.invert_y = True
            const.use_x = False
            const.use_y = True
            const.use_z = False

        return {'FINISHED'}

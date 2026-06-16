import math

import bpy
from mathutils import Vector
from ..rig_generator import RigGenerator, Point


class GeneratorLegsHandsIK(RigGenerator):
    def create_ik_chain(self, bones: list[str], collection_path: str, collection_name: str, pole_side: float = 1,
                        target_shape: str = 'WGT-Hand'):
        obj = self.get_obj()
        arm: bpy.types.Armature = obj.data
        edit_bs = arm.edit_bones

        collection_stretch = f'{collection_path}/{collection_name} Stretch'
        collection_ik = f'{collection_path}/{collection_name} IK'

        self.start_edit()
        points: list[Point] = []
        copy_location: list[tuple[str, str]] = []
        prev_point = None

        for index, bone in enumerate(bones):
            current: bpy.types.EditBone = self.get_edit_bone(bone)

            point = Point(
                head=current.head,
                tail=current.tail,
                name=bone,
                is_end=index >= len(bones) - 1,
                prev=prev_point
            )

            if prev_point is not None:
                prev_point.next = point

            prev_point = point
            points.append(point)

        # Generate STR bones
        str_constraints: list[tuple[str, str]] = []

        for point in points:
            if point.next is None:
                str_bone = edit_bs.new(f'STR_Control_{point.name}')
                str_bone.head = point.head
                str_bone.tail = point.head - Vector((0, 0, 0.05))
                str_bone.parent = self.get_edit_bone(f'MCH_{point.prev.name}')
                self.apply_widget_sphere(str_bone.name)
                self.add_to_collection(str_bone.name, collection_stretch)
                continue

            mch_bone = edit_bs.new(f'MCH_{point.name}')
            mch_bone.head = point.head
            mch_bone.tail = point.next.head

            str_mch_bone = edit_bs.new(f'STR_{point.name}')
            str_mch_bone.head = point.head
            str_mch_bone.tail = point.next.head
            self.add_to_collection(str_mch_bone.name, f'MCH')

            # Stretch bone
            str_bone = edit_bs.new(f'STR_Control_{point.name}')
            str_bone.head = point.head
            str_bone.tail = point.head - Vector((0, 0, 0.05))
            str_bone.parent = mch_bone
            str_mch_bone.parent = str_bone

            str_constraints.append((str_mch_bone.name, f'STR_Control_{point.next.name}'))

            self.apply_widget_sphere(str_bone.name)
            self.add_to_collection(str_bone.name, collection_stretch)

            if point.prev:
                prev_bone = self.get_edit_bone(f'MCH_{point.prev.name}')
                mch_bone.parent = prev_bone

        # Generate ORG bones
        copy_transforms: list[tuple[str, str]] = []
        for point in points:
            if point.next is None: continue
            str_mch_bone = edit_bs.new(f'ORG_{point.name}')
            str_mch_bone.head = point.head
            str_mch_bone.tail = point.next.head

            org_s: bpy.types.EditBone = self.get_edit_bone(self.dup_bone(f'ORG_S_', point.name))
            org_s.parent = str_mch_bone

            copy_transforms.append((org_s.name, point.name))
            copy_transforms.append((f'STR_{point.name}', str_mch_bone.name))

            if point.prev:
                prev_bone = self.get_edit_bone(f'ORG_{point.prev.name}')
                str_mch_bone.parent = prev_bone

        # Generate IK bones
        ik_end = ''
        ik_target = ''
        pole_target = ''
        copy_rotations: list[tuple[str, str]] = []

        copy_scales: list[tuple[str, str, tuple[str, ...]]] = []
        ik_bones: list[str] = []

        for point in points:
            # Target Pole Bone
            if point.prev is None:
                b = self.get_edit_bone(f'MCH_{point.name}')
                pole_bone = edit_bs.new(f'POLL_{point.name}')
                pole_bone.head = b.tail - Vector((0, 0, .25 * pole_side))
                pole_bone.tail = b.tail - Vector((0, 0, .3 * pole_side))
                pole_target = pole_bone.name

                line = edit_bs.new(f'LINE_{point.name}')
                line.head = b.tail
                line.tail = pole_bone.head
                line.parent = self.get_edit_bone(f'STR_{point.name}')

                str_constraints.append((line.name, pole_target))
                self.set_non_selectable(line.name)

                self.apply_widget(line.name, 'WGT-Line')

                self.parent_to_root(pole_target)
                self.apply_widget_sphere(pole_bone.name)
                self.add_to_collection(line.name, collection_ik)
                self.add_to_collection(pole_bone.name, collection_ik)

            # Target Bone
            if point.next is None:
                ik_end = f'IK_{point.prev.name}'
                ik_target = self.dup_bone('TGT_', point.name)
                copy_rotations.append((f'TGT_{point.name}', point.name))
                copy_scales.append((f'TGT_{point.name}', point.name, ('x', 'y', 'z')))

                self.parent_to_root(ik_target)
                self.apply_widget(ik_target, target_shape)
                self.add_to_collection(ik_target, collection_ik)
                continue

            main_ik = edit_bs.new(f'IK_{point.name}')
            main_ik.head = point.head
            main_ik.tail = point.next.head
            ik_bones.append(main_ik.name)

            copy_rotations.append((main_ik.name, f'MCH_{point.name}'))
            copy_location.append((main_ik.name, f'MCH_{point.name}'))
            copy_scales.append((main_ik.name, f'MCH_{point.name}', ('y',)))

            if point.prev:
                prev_bone = self.get_edit_bone(f'IK_{point.prev.name}')
                main_ik.parent = prev_bone
            else:
                ik_start = f'IK_{point.name}'
                self.get_edit_bone(ik_start).parent = self.get_edit_bone(point.name).parent

        self.end_edit()

        # Constraint bind

        ik = self.get_pose_bone(ik_end)
        ik: bpy.types.KinematicConstraint = ik.constraints.new('IK')
        ik.target = obj
        ik.subtarget = ik_target
        ik.pole_target = obj
        ik.pole_subtarget = pole_target
        ik.pole_angle = -math.pi / 2
        ik.chain_count = 2

        for to, from_ in str_constraints:
            self.create_stretch_to(from_, to, 1)

        for from_, to in copy_transforms:
            self.create_copy_transform(from_, to, 1)

        for from_, to in copy_rotations:
            self.create_copy_rotation(from_, to, 1)

        for from_, to in copy_location:
            self.create_copy_location(from_, to, 1)

        for bone in ik_bones:
            p_bone = self.get_pose_bone(bone)
            p_bone.ik_stretch = 0.001

        for from_, to, coord in copy_scales:
            self.create_copy_scale(from_, to, 1, use=coord)

    def execute(self, context: bpy.types.Context):
        bpy.ops.object.mode_set(mode='POSE')

        for side in ['L', 'R']:
            self.create_ik_chain([
                f'cf_J_ArmUp00_{side}',
                f'cf_J_ArmLow01_{side}',
                f'cf_J_Hand_s_{side}'
            ],
                collection_path='Hands',
                collection_name=f'Hand {'Right' if side == 'L' else 'Left'}',
                target_shape=f'WGT-Hand_{side}'
            )

        for side in ['L', 'R']:
            self.create_ik_chain([
                f'cf_J_LegUp00_{side}',
                f'cf_J_LegLow01_{side}',
                f'cf_J_Foot01_{side}'
            ],
                collection_path='Legs',
                collection_name=f'Leg {'Right' if side == 'L' else 'Left'}',
                pole_side=-1,
                target_shape=''
            )

        self.start_edit()
        dumped_track: list[tuple[str, str]] = []
        for side in ['L', 'R']:
            toes_name = f'cf_J_Toes01_{side}'
            foot_name = f'cf_J_Foot01_{side}'

            tgt = self.get_edit_bone(f'TGT_{foot_name}')

            toes_target = self.get_edit_bone(self.dup_bone('MCH_TOES_TGT_', toes_name))

            roll = self.get_edit_bone(self.dup_bone('ROLL_', toes_name))
            roll_revers = self.get_edit_bone(self.dup_bone('ROLL_REVERS_', f'cf_J_Foot02_{side}'))

            toes_ctr = self.get_edit_bone(self.dup_bone('CTR_', toes_name))

            main = self.get_edit_bone(self.dup_bone('TGT_Main_', foot_name))
            main.parent = self.get_edit_bone('cf_N_height')

            toes_target.tail += Vector((0, 0, .04))
            toes_target.head += Vector((0, 0, .04))
            toes_target.tail -= Vector((0, toes_target.length / 2, 0))
            dumped_track.append((toes_name, toes_target.name))

            roll_revers.tail -= Vector((0, 0, .03))
            roll_revers.head -= Vector((0, 0, .03))
            roll_revers.head.y = 0.01
            roll_revers.tail.y = 0.1
            # roll_revers.tail -= Vector((0, toes_target.length / 2, 0))

            tgt.parent = roll
            roll.parent = roll_revers

            toes_ctr.parent = roll_revers
            toes_target.parent = toes_ctr

            roll_revers.parent = main

            self.apply_widget(toes_ctr.name, f'WGT-Toes_{side}')
            self.apply_widget(roll.name, f'WGT-FootRoll')
            self.apply_widget(roll_revers.name, f'WGT-FootRollRevers')

            self.add_to_collection(roll.name, 'Legs/Foot')
            self.add_to_collection(roll_revers.name, 'Legs/Foot')
            self.add_to_collection(toes_ctr.name, 'Legs/Foot')

            self.apply_widget(main.name, 'WGT-Foot')

        self.end_edit()

        for from_, to in dumped_track:
            self.create_dumped_track(from_, to, 'TRACK_Z')

        self.apply_all()

        self.start_edit()
        for side in ['L', 'R']:
            foot_name = f'cf_J_Foot01_{side}'

            tgt = self.get_edit_bone(f'TGT_{foot_name}')
            tgt.name = f'MCH_TGT_{foot_name}'

        self.end_edit()
        return {'FINISHED'}

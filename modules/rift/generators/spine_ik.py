import bpy
from mathutils import Vector

from ..rig_generator import RigGenerator, Point


class GeneratorSpineIK(RigGenerator):

    def execute(self, context: bpy.types.Context):
        self.start_edit()
        obj = self.get_obj()
        arm: bpy.types.Armature = obj.data
        edit_bs = arm.edit_bones
        bones = ['cf_J_Spine01', 'cf_J_Spine02', 'cf_J_Spine03', 'cf_J_Neck']

        points: list[Point] = []

        prev_point = None
        copy_transforms: list[tuple[str, str]] = []
        copy_rotation: list[tuple[str, str]] = []

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

        # Generate ORG bones
        chest_override = ''
        for point in points:
            if point.next is None:
                bone = edit_bs.new(f'MCH_End_{point.name}')
                bone.head = point.head
                bone.tail = point.head + Vector((0, 0, -.1))
                bone.parent = self.get_edit_bone(point.prev.name)
                chest_override = bone.name
                continue
            mch_bone = edit_bs.new(f'CTR_{point.name}')
            mch_bone.head = point.head
            mch_bone.tail = point.next.head
            self.add_to_collection(mch_bone.name, 'Spine')

            org_s: bpy.types.EditBone = self.get_edit_bone(self.dup_bone(f'ORG_S_', point.name))
            org_s.parent = mch_bone

            copy_transforms.append((org_s.name, point.name))
            self.apply_widget(mch_bone.name, 'WGT-Spine')

            if point.prev:
                prev_bone = self.get_edit_bone(f'CTR_{point.prev.name}')
                mch_bone.parent = prev_bone

            if point.prev is None:
                parent = self.get_edit_bone(point.name).parent
                bone = edit_bs.new('CTR_Spine')
                bone.head = point.head
                bone.tail = point.tail
                bone.parent = parent

                bone = self.get_edit_bone(f'CTR_{point.name}')
                bone.parent = parent

                self.apply_widget('CTR_Spine', 'WGT-Chest')
                self.add_to_collection('CTR_Spine', 'Spine')

        for point in points:
            if point.next is None:
                continue
            org_name = f'CTR_{point.name}'

            copy_rotation.append(('CTR_Spine', org_name))

        self.end_edit()

        for from_, to in copy_transforms:
            self.create_copy_transform(from_, to, 1)

        for from_, to in copy_rotation:
            rot = self.create_copy_rotation(from_, to, .5)
            rot.owner_space = 'LOCAL'
            rot.target_space = 'LOCAL'
            rot.mix_mode = 'ADD'

        self.apply_all()

        bone = self.get_pose_bone('CTR_Spine')
        bone.custom_shape_transform = self.get_pose_bone(chest_override)
        return {'FINISHED'}

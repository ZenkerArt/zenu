import bpy.types
from mathutils import Vector

from ..rig_generator import RigGenerator
EYE_TARGET_NAME = 'TGT_EyeTarget'

class GeneratorEyeTarget(RigGenerator):
    def create_eye_target(self, eye_bone: str, target_bone: str):
        self.start_edit()
        e_eye = self.get_edit_bone(eye_bone)
        e_main_target = self.get_edit_bone(target_bone)

        e_eye_target = self.get_edit_bone(self.dup_bone(f'TGT_', e_eye.name))
        e_eye_target.head.z = e_main_target.head.z
        e_eye_target.tail.z = e_main_target.head.z

        e_eye_target.parent = e_main_target

        dumped_track = [
            (e_eye.name, e_eye_target.name)
        ]

        self.apply_widget(e_eye_target.name, 'WGT-Eye')
        self.end_edit()

        for from_, to in dumped_track:
            self.create_dumped_track(from_, to, 'TRACK_Z')

    def execute(self, context: bpy.types.Context):
        eye_l_name = 'cf_J_eye_rs_L'
        eye_r_name = 'cf_J_eye_rs_R'
        target_name = EYE_TARGET_NAME

        self.start_edit()
        e_eye_l = self.get_edit_bone(eye_l_name)
        e_eye_r = self.get_edit_bone(eye_r_name)

        pos_l = e_eye_l.head
        pos_r = e_eye_r.head
        center = pos_l.lerp(pos_r, 0.5)

        target_bone = self.create_bone(target_name)
        target_bone.head = center + Vector((0, 0, .2))
        target_bone.tail = center + Vector((0, .02, .2))
        self.apply_widget(target_bone.name, 'WGT-EyeTarget')


        self.end_edit()

        self.create_eye_target(eye_l_name, target_name)
        self.create_eye_target(eye_r_name, target_name)

        self.apply_all()

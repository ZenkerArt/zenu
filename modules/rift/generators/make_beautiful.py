from ..rig_generator import RigGenerator
import bpy


class GeneratorMakeBeautiful(RigGenerator):
    def execute(self, context: bpy.types.Context):
        rigging = self.get_collection('Rigging')

        c = self.get_collection('Original')
        c.parent = rigging
        c = self.get_collection('MCH')
        c.parent = rigging
        c = self.get_collection('ORG')
        c.parent = rigging

        for bone in self.get_obj().pose.bones:
            try:
                n = bone.name

                if n.startswith('MCH') or n.startswith('IK'):
                    self.add_to_collection(bone.name, 'Rigging/MCH')

                if n.startswith('ORG'):
                    self.add_to_collection(bone.name, 'Rigging/ORG')

                if n.startswith('cf'):
                    self.add_to_collection(bone.name, 'Rigging/Original')

                if n.startswith('CORRECTIVE'):
                    self.add_to_collection(bone.name, 'Rigging/Correction')
            except IndexError:
                pass

        for side in ['L', 'R']:
            self.apply_widget(f'cf_J_Shoulder_{side}', f'WGT-Shoulder_{side}')
            self.apply_widget(f'cf_J_SiriDam_{side}', f'WGT-Butt_{side}')

            self.add_to_collection(f'cf_J_Shoulder_{side}', 'Hands/Shoulders')
            self.add_to_collection(f'cf_J_SiriDam_{side}', 'Extra')

            for finger in ['Little', 'Ring', 'Middle', 'Index', 'Thumb']:
                for index in range(2, 4):
                    full_finger = f'cf_J_Hand_{finger}0{index}_{side}'

                    self.add_to_collection(full_finger, f'Fingers/Fingers {side}')
                    self.apply_widget(full_finger, 'WGT-Finger')

        self.apply_widget('cf_J_Neck', 'WGT-Neck')
        self.apply_widget('cf_J_FaceBase', 'WGT-FaceRoot')
        self.apply_widget('cf_N_height', 'WGT-Root')
        self.apply_widget('cf_J_Kokan', 'WGT-Vagina')
        self.apply_widget('cf_J_Ana', 'WGT-Anus')
        self.apply_widget('cf_J_Hips', 'WGT-Hips')
        self.apply_widget('cf_J_Kosi01', 'WGT-Hip')

        self.add_to_collection('cf_J_Neck', 'Head')
        self.add_to_collection('cf_J_FaceBase', 'Head')
        self.add_to_collection('cf_N_height', 'Root')
        self.add_to_collection('cf_J_Kokan', 'Extra')
        self.add_to_collection('cf_J_Ana', 'Extra')
        self.add_to_collection('cf_J_Kosi01', 'Spine')
        self.add_to_collection('cf_J_Hips', 'Spine')

        self.apply_all()

        self.get_collection('Head').child_number = -1000
        self.get_collection('Hands').child_number = -1000
        self.get_collection('Fingers').child_number = -1000
        self.get_collection('Spine').child_number = -1000
        self.get_collection('Legs').child_number = -1000
        self.get_collection('Extra').child_number = -1000
        self.get_collection('Root').child_number = -1000
        self.get_collection('Rigging').child_number = -1000

        for collection in self.get_collection_all():
            for bone in collection.bones_recursive:
                if collection.name.endswith('IK'):
                    bone.color.palette = 'THEME01'

                if collection.name.endswith('Stretch'):
                    bone.color.palette = 'THEME03'

        for bone in self.get_collection('Spine').bones_recursive:
            bone.color.palette = 'THEME09'
        for bone in self.get_collection('Extra').bones_recursive:
            bone.color.palette = 'THEME11'
        for bone in self.get_collection('Fingers').bones_recursive:
            bone.color.palette = 'THEME09'
        for bone in self.get_collection('Shoulders').bones_recursive:
            bone.color.palette = 'THEME09'
        for bone in self.get_collection('Head').bones_recursive:
            bone.color.palette = 'THEME09'
        return {'FINISHED'}

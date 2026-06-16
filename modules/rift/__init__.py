import bpy
from bpy.types import UIList

from .generators.correction import GeneratorCorrection
from .generators.eye_target import GeneratorEyeTarget
from .generators.face_emotions import GeneratorFaceEmotion
from .generators.fingers import GeneratorFingers
from .generators.hand_legs_ik import GeneratorLegsHandsIK
from .generators.make_beautiful import GeneratorMakeBeautiful
from .generators.spine_ik import GeneratorSpineIK
from .rig_generator import RigGenerator
from ...base_panel import RiftBasePanel


class SK_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        row.prop(item, "name", text='', emboss=False)
        row.prop(item, "value", text='', emboss=False)


class ZENU_OT_create_correction(bpy.types.Operator, RigGenerator):
    bl_label = 'Create Correction'
    bl_idname = 'zenu.create_correction'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorCorrection().execute(context)

        return {'FINISHED'}


class ZENU_OT_create_legs_hands_ik(bpy.types.Operator, RigGenerator):
    bl_label = 'Create Legs/Hands IK'
    bl_idname = 'zenu.create_legs_hands_ik'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorLegsHandsIK().execute(context)
        return {'FINISHED'}


class ZENU_OT_create_spine_ik(bpy.types.Operator, RigGenerator):
    bl_label = 'Create Spine IK'
    bl_idname = 'zenu.create_spine_ik'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorSpineIK().execute(context)
        return {'FINISHED'}


class ZENU_OT_create_fingers(bpy.types.Operator, RigGenerator):
    bl_label = 'Create Fingers'
    bl_idname = 'zenu.create_fingers'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorFingers().execute(context)
        return {'FINISHED'}


class ZENU_OT_create_eye_target(bpy.types.Operator):
    bl_label = 'Create Eye Target'
    bl_idname = 'zenu.create_eye_target'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorEyeTarget().execute(context)
        return {'FINISHED'}


class ZENU_OT_create_face_emotions(bpy.types.Operator):
    bl_label = 'Create Face Emotions'
    bl_idname = 'zenu.create_face_emotions'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorFaceEmotion().execute(context)
        return {'FINISHED'}


class ZENU_OT_make_beautiful(bpy.types.Operator, RigGenerator):
    bl_label = 'Make Beautiful'
    bl_idname = 'zenu.make_beautiful'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        GeneratorMakeBeautiful().execute(context)
        return {'FINISHED'}


class ZENU_PT_rift(RiftBasePanel):
    bl_label = 'Rift'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_create_correction.bl_idname)
        layout.operator(ZENU_OT_create_legs_hands_ik.bl_idname)
        layout.operator(ZENU_OT_create_spine_ik.bl_idname)
        layout.operator(ZENU_OT_create_fingers.bl_idname)

        box = layout.box()
        box.operator(ZENU_OT_create_eye_target.bl_idname)
        box.operator(ZENU_OT_create_face_emotions.bl_idname)

        layout.operator(ZENU_OT_make_beautiful.bl_idname)

        obj = bpy.data.objects['Lyriel_cf_O_body']

        layout.template_list(
            "SK_UL_List",
            "",
            obj.data.shape_keys,
            "key_blocks",
            obj,
            "active_shape_key_index"
        )


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_create_correction,
    ZENU_OT_create_legs_hands_ik,
    ZENU_OT_create_spine_ik,
    ZENU_OT_create_fingers,
    ZENU_OT_create_eye_target,
    ZENU_OT_create_face_emotions,
    ZENU_OT_make_beautiful,
    SK_UL_List,
    ZENU_PT_rift,
))


def register():
    reg()


def unregister():
    unreg()

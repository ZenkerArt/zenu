import bpy
from ...utils import is_type, get_modifier, get_all_modifiers, check_mods


class ZENU_OT_select_parent_objects(bpy.types.Operator):
    bl_label = 'Select Parent Objects'
    bl_idname = 'zenu.select_parent_objects'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        state = True

        try:
            for selected_object in context.selected_objects:

                for obj in bpy.data.objects:
                    if not is_type(obj, bpy.types.Mesh):
                        continue

                    mod: list[bpy.types.ArmatureModifier] = get_modifier(obj, bpy.types.ArmatureModifier)
                    state = state and mod.object.data == selected_object.data and mod is not None
        except Exception:
            return False

        return not is_type(context.object, bpy.types.Mesh) and state

    def execute(self, context: bpy.types.Context):
        for selected_object in context.selected_objects:

            for obj in bpy.data.objects:
                if not is_type(obj, bpy.types.Mesh):
                    continue

                mod: list[bpy.types.ArmatureModifier] = get_modifier(obj, bpy.types.ArmatureModifier)
                if mod is None:
                    continue

                if mod.object.data == selected_object.data:
                    obj.select_set(True)
        return {'FINISHED'}


class ZENU_OT_select_bones(bpy.types.Operator):
    bl_label = 'Select Bones'
    bl_idname = 'zenu.select_bones'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        state = True

        try:
            for obj in context.selected_objects:
                if not is_type(obj, bpy.types.Mesh):
                    continue

                mods: bpy.types.ArmatureModifier = get_all_modifiers(obj, bpy.types.ArmatureModifier)
                state = state and mods
        except Exception:
            return False

        return is_type(context.object, bpy.types.Mesh) and state and check_mods('o')

    def execute(self, context: bpy.types.Context):
        selected_object = []

        for obj in context.selected_objects:
            if not is_type(obj, bpy.types.Mesh):
                continue

            mods: bpy.types.ArmatureModifier = get_all_modifiers(obj, bpy.types.ArmatureModifier)

            for mod in mods:
                selected_object.append(mod.object)

        for obj in context.selected_objects:
            obj.select_set(False)

        for obj in selected_object:
            obj.select_set(True)
            context.view_layer.objects.active = obj

        return {'FINISHED'}


classes = [
    ZENU_OT_select_bones,
    ZENU_OT_select_parent_objects
]

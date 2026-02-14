import bpy
bl_info = {
    "name": "Create Pose Asset From Current Frame",
    "author": "Zenker",
    "version": (2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Pose Assets",
    "description": "",
    "category": "Animation",
}


class POSE_OT_create_asset_from_frame(bpy.types.Operator):
    bl_idname = "pose.create_asset_from_frame"
    bl_label = "Create Pose Asset From Current Frame"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):

        obj: bpy.types.Object = context.object

        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select Armature")
            return {'CANCELLED'}

        frame = context.scene.frame_current
        prev_action = obj.animation_data.action
        action = prev_action.copy()

        bpy.ops.object.mode_set(mode='POSE')

        obj.animation_data.action = action
        name = f"Pose_F{frame}"
        action.name = name

        prev_frame = context.scene.frame_current
        try:
            for space in context.area.spaces:
                if space.type == 'DOPESHEET_EDITOR':
                    space.dopesheet.show_only_selected = False
                    space.dopesheet.show_only_slot_of_active_object = False
                    space.dopesheet.show_hidden = True
        except Exception:
            pass

        bpy.ops.action.select_all(action='DESELECT')
        bpy.ops.action.select_column(mode='CFRA')
        bpy.ops.action.select_all(action='INVERT')
        bpy.ops.action.delete()

        bpy.ops.action.select_column(mode='CFRA')

        context.scene.frame_current = 1
        bpy.ops.action.snap(type='CFRA')
        

        action.asset_mark()
        bpy.ops.ed.lib_id_generate_preview()
        
        obj.animation_data.action = prev_action
        context.scene.frame_current = prev_frame

        self.report({'INFO'}, f"Pose asset created at frame {frame}")
        return {'FINISHED'}


class POSE_PT_panel(bpy.types.Panel):
    bl_label = "Pose Assets"
    bl_idname = "POSE_PT_assets"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Pose Assets"

    def draw(self, context):
        layout = self.layout
        layout.operator("pose.create_asset_from_frame", icon='ASSET_MANAGER')


reg, unreg = bpy.utils.register_classes_factory((
    POSE_OT_create_asset_from_frame,
    POSE_PT_panel,
))


def register():
    reg()


def unregister():
    unreg()


if __name__ == "__main__":
    register()

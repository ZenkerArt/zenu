import bpy
from ...base_panel import BasePanel
from ...utils import check_mods


class ZENU_OT_create_keying_set_from_selected(bpy.types.Operator):
    bl_label = 'Create Keying Set From Selected'
    bl_idname = 'zenu.create_keying_set_from_selected'
    bl_options = {'UNDO'}
    channels: bpy.props.EnumProperty(
        items=(
            ('LOCATION', 'Location', ''),
            ('ROTATION', 'Rotation', ''),
            ('SCALE', 'Scale', ''),
        ),
        options={'ENUM_FLAG'},
        name='Channels',
        default={'ROTATION', 'LOCATION', 'SCALE'})

    def invoke(self, context, event):
        context.scene.zenu_material_selector_slot = None
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        col = layout.column(align=True)
        col.prop(self, 'channels')

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return check_mods('p')

    def execute(self, context: bpy.types.Context):
        obj = context.active_object

        print(self.channels)

        keying_set = bpy.context.scene.keying_sets.new()

        def add_path(name: str, typ: str):
            path = keying_set.paths.add(obj, f'pose.bones["{name}"].{typ}')
            path.group_method = 'NAMED'
            path.group = name

        for bone in context.selected_pose_bones:
            if 'LOCATION' in self.channels:
                add_path(bone.name, 'location')

            if bone.rotation_mode == 'QUATERNION' and 'ROTATION' in self.channels:
                add_path(bone.name, 'rotation_quaternion')
            elif 'ROTATION' in self.channels:
                add_path(bone.name, 'rotation_euler')

            if 'SCALE' in self.channels:
                add_path(bone.name, 'scale')

        return {'FINISHED'}


class ZENU_PT_animation_utils_keying_set(BasePanel):
    bl_label = 'Animation Utils'
    bl_context = ''

    def keying_set_panel(self, context):
        layout = self.layout

        scene = context.scene

        row = layout.row()

        col = row.column()
        col.template_list("UI_UL_list", "keying_sets", scene, "keying_sets", scene.keying_sets, "active_index", rows=1)

        col = row.column(align=True)
        col.operator("anim.keying_set_add", icon='ADD', text="")
        col.operator("anim.keying_set_remove", icon='REMOVE', text="")

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        flow = layout.grid_flow(row_major=False, columns=0, even_columns=False, even_rows=False, align=False)

        ks = scene.keying_sets.active
        if ks and ks.is_path_absolute:
            col = flow.column()
            col.prop(ks, "bl_description")

            subcol = flow.column()
            subcol.operator_context = 'INVOKE_DEFAULT'
            subcol.operator("anim.keying_set_export", text="Export to File").filepath = "keyingset.py"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        self.keying_set_panel(context)
        layout.operator(ZENU_OT_create_keying_set_from_selected.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_create_keying_set_from_selected,
    ZENU_PT_animation_utils_keying_set
))


def register():
    reg()


def unregister():
    unreg()

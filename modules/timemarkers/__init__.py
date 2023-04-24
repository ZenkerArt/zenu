import bmesh
import bpy
from bpy.types import Context
from ...base_panel import BasePanel
from ...utils import check_mods
from ...keybindings import keybindings, Keybinding, add_binding


class ZENU_UL_physic_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')


class ZENU_OT_time_create_spaces(bpy.types.Operator):
    bl_label = 'Time Create Spaces'
    bl_idname = 'zenu.time_create_spaces'
    bl_options = {'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    value: int
    _spaces: int = 4

    @property
    def spaces(self):
        return self._spaces

    @spaces.setter
    def spaces(self, value: int):
        if value <= 0:
            return
        self._spaces = value

    def execute(self, context: bpy.types.Context):
        end_frame = 5 * int((self.value - self.init_loc_x) / 25)
        current_frame = context.scene.frame_current
        spaces = self.spaces

        scene = context.scene

        space_length = (end_frame - current_frame) / spaces

        for i in range(spaces):
            view = int(space_length * i) + 1
            keyframe = int(space_length * i) + context.scene.frame_current
            scene.timeline_markers.new(f'SP_{view}', frame=keyframe)

        scene.timeline_markers.new(f'SP_{end_frame}', frame=end_frame)

        return {'FINISHED'}

    def clear(self, context: bpy.types.Context):
        scene = context.scene
        for item in scene.timeline_markers:
            if not item.name.startswith('SP_'):
                continue

            scene.timeline_markers.remove(item)

    def update(self, context: bpy.types.Context):
        self.clear(context)
        self.execute(context)

    def modal(self, context: bpy.types.Context, event):
        if event.type == 'WHEELDOWNMOUSE':
            self.spaces -= 1
            self.update(context)
        elif event.type == 'WHEELUPMOUSE':
            self.spaces += 1
            self.update(context)

        if event.type == 'MOUSEMOVE':  # Apply
            self.value = event.mouse_x
            self.update(context)
        elif event.type == 'LEFTMOUSE':  # Confirm
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            self.clear(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc_x = event.mouse_x
        self.value = event.mouse_x
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class ZENU_PT_time_markers(BasePanel):
    bl_label = 'Time Markers'
    bl_context = ''

    # @classmethod
    # def poll(cls, context: 'Context'):
    #     return check_mods('op')

    def draw(self, context: Context):
        layout = self.layout
        layout.operator(ZENU_OT_time_create_spaces.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_time_create_spaces,
    ZENU_PT_time_markers,
))

def register():
    key_config = bpy.context.window_manager.keyconfigs.addon
    if key_config:
        key_map = key_config.keymaps.new(name='3D View', space_type='VIEW_3D')
        key_entry = key_map.keymap_items.new(ZENU_OT_time_create_spaces.bl_idname,
                                             type='W',
                                             value='PRESS',
                                             # ctrl=True,
                                             )

        add_binding(key_entry)
    reg()


def unregister():
    unreg()

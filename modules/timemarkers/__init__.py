import math

import bpy
from bpy.types import Context
from ...base_panel import BasePanel
from ...keybindings import dopesheet, graph_editor


class ZENU_UL_physic_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')


class ZENU_OT_time_create_spaces(bpy.types.Operator):
    bl_label = 'Time Create Spaces'
    bl_idname = 'zenu.time_create_spaces'
    bl_options = {'UNDO', 'UNDO_GROUPED', 'GRAB_CURSOR', 'BLOCKING'}
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
        current_frame = context.scene.frame_current
        end_frame = current_frame + 5 * int((self.value - self.init_loc_x) / 25)
        spaces = self.spaces

        scene = context.scene

        space_length = (end_frame - current_frame) / spaces
        view = 0
        for i in range(1, spaces):
            view = int(space_length * i)

            keyframe = int(space_length * i) + context.scene.frame_current
            if current_frame == 1:
                keyframe -= 1

            scene.timeline_markers.new(f'SP_{view}', frame=keyframe)

        scene.timeline_markers.new(f'SP_1', frame=current_frame)
        scene.timeline_markers.new(f'SP_{math.ceil(view + space_length)}',
                                   frame=end_frame - 1 if current_frame == 1 else end_frame)

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
    # ZENU_PT_time_markers,
))


def register():
    dopesheet.new(ZENU_OT_time_create_spaces.bl_idname, type='W', value='PRESS')
    graph_editor.new(ZENU_OT_time_create_spaces.bl_idname, type='W', value='PRESS')
    reg()


def unregister():
    unreg()

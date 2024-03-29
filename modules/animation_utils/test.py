from typing import Any

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from ..context_pie import pie_menu_context
from ...utils import update_window
from ...base_panel import BasePanel


class Drawer:
    _render: Any = None
    start_x: int = 0
    end_x: int = 0

    def draw(self):
        vertices = (
            (self.start_x, 100), (self.end_x, 100),
            (self.start_x, 200), (self.end_x, 200))

        indices = (
            (0, 1, 2), (2, 1, 3))

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
        batch.draw(shader)

    def activate(self):
        if self._render is None:
            update_window()
            self._render = bpy.types.SpaceGraphEditor.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
            update_window()
            return

    def deactivate(self):
        if self._render is None:
            return

        bpy.types.SpaceGraphEditor.draw_handler_remove(self._render, 'WINDOW')
        self._render = None
        update_window()

    def toggle(self):
        if self._render is None:
            self.activate()
        else:
            self.deactivate()

    def __del__(self):
        self.deactivate()


draw = Drawer()


class ZENU_PT_test_anim_panel(BasePanel):
    bl_label = 'Animation Test'
    bl_space_type = 'GRAPH_EDITOR'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_anim_enable.bl_idname)
        # x, y = context.region.view2d.region_to_view(self.mouse_x, 0)


class ZENU_OT_anim_enable(bpy.types.Operator):
    bl_label = 'Noise Remove'
    bl_idname = 'zenu.anim_enable'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            x, y = event.mouse_region_x, event.mouse_region_y
            draw.end_x = x
            self.execute(context)
            update_window()
        elif event.type == 'LEFTMOUSE':
            draw.deactivate()
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            draw.deactivate()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        draw.start_x = pie_menu_context.mouse_region_x
        draw.activate()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


classes = (
    ZENU_PT_test_anim_panel,
    ZENU_OT_anim_enable
)

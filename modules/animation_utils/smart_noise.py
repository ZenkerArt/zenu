import bpy
from ..context_pie import pie_menu_context
from ...utils import update_window


def poll(context: bpy.types.Context):
    fcurve = context.active_editable_fcurve

    if fcurve is None:
        return False

    return select_current_mod(fcurve, context)


def select_nearest_mod(fcurve: bpy.types.FCurve, context: bpy.types.Context, x: int):
    x, y = context.region.view2d.region_to_view(x, 0)

    for mod in fcurve.modifiers:
        if not isinstance(mod, bpy.types.FModifierNoise): continue

        start = mod.frame_start
        end = mod.frame_end
        if start < x < end:
            return mod
    return None


def select_side(mod: bpy.types.FModifierNoise, x: int):
    return abs(mod.frame_end - x) > abs(x - mod.frame_start)


def select_current_mod(fcurve: bpy.types.FCurve, context: bpy.types.Context):
    return select_nearest_mod(fcurve, context, pie_menu_context.mouse_region_x)


class ZENU_PT_mod_panel(bpy.types.Panel):
    bl_idname = 'ZENU_PT_mod_panel'
    bl_label = 'Mod Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        fcurve = context.active_editable_fcurve
        mod = fcurve.modifiers.active
        col = layout.column(align=True)
        col.scale_y = 1.4
        col.prop(mod, 'scale')
        col.prop(mod, 'strength')
        col.prop(mod, 'offset')
        col.prop(mod, 'phase')


class ZENU_OT_anim_noise_property_edit(bpy.types.Operator):
    bl_label = 'Noise Property Menu'
    bl_idname = 'zenu.anim_noise_property_edit'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll(context)

    def execute(self, context: bpy.types.Context):
        fcurve = context.active_editable_fcurve
        mod = select_current_mod(fcurve, context)
        mod.active = True

        fcurve.update()
        update_window(True)

        bpy.ops.wm.call_panel(name=ZENU_PT_mod_panel.bl_idname)
        return {'FINISHED'}


class ZENU_OT_anim_noise(bpy.types.Operator):
    bl_label = 'Noise'
    bl_idname = 'zenu.anim_noise'
    bl_options = {'UNDO'}
    mod: bpy.types.FModifierNoise
    is_start: bool = True
    init_mouse_x: int = 0
    mouse_x: int = 0

    def execute(self, context: bpy.types.Context):
        x, y = context.region.view2d.region_to_view(self.mouse_x, 0)
        if self.is_start:
            self.mod.frame_start = x
            self.mod.frame_end = x
        else:
            self.mod.frame_end = x
        return {'FINISHED'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_region_x
            self.execute(context)
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self.is_start:
                self.is_start = False
            else:
                return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            fcurve = context.active_editable_fcurve
            fcurve.modifiers.remove(self.mod)
            fcurve.update()
            update_window(True)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_mouse_x = event.mouse_x
        self.is_start = True
        fcurve = context.active_editable_fcurve
        self.mod: bpy.types.FModifierNoise = fcurve.modifiers.new('NOISE')
        self.mod.use_restricted_range = True
        fcurve.update()
        update_window(True)

        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class ZENU_OT_anim_noise_blend(bpy.types.Operator):
    bl_label = 'Noise Blend'
    bl_idname = 'zenu.anim_noise_blend'
    bl_options = {'UNDO'}
    mod: bpy.types.FModifierNoise
    is_start: bool = True
    init_mouse_x: int = 0
    mouse_x: int = 0
    blend_in: float = 0
    blend_out: float = 0

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll(context)

    def execute(self, context: bpy.types.Context):
        x, y = context.region.view2d.region_to_view(self.mouse_x, 0)
        start_x = x - self.mod.frame_start
        end_x = self.mod.frame_end - x

        if self.is_start:
            self.mod.blend_in = start_x
        else:
            self.mod.blend_out = end_x
        return {'FINISHED'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_region_x
            self.execute(context)
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.mod.blend_in = self.blend_in
            self.mod.blend_out = self.blend_out
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_mouse_x = event.mouse_x
        self.is_start = True
        fcurve = context.active_editable_fcurve
        x, y = context.region.view2d.region_to_view(pie_menu_context.mouse_region_x, pie_menu_context.mouse_region_y)

        mod = select_current_mod(fcurve, context)

        if mod is None:
            return {'CANCELLED'}

        self.is_start = select_side(mod, x)

        self.mod = mod
        self.blend_in = self.mod.blend_in
        self.blend_out = self.mod.blend_out
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class ZENU_OT_anim_noise_edit(bpy.types.Operator):
    bl_label = 'Noise Edit'
    bl_idname = 'zenu.anim_noise_edit'
    bl_options = {'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    mod: bpy.types.FModifierNoise
    is_start: bool = True
    init_mouse_x: int = 0
    mouse_x: int = 0
    frame_start: float = 0
    frame_end: float = 0

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll(context)

    def execute(self, context: bpy.types.Context):
        x, y = context.region.view2d.region_to_view(self.mouse_x, 0)
        init_x, y = context.region.view2d.region_to_view(self.init_mouse_x, 0)
        self.mod.frame_start = self.frame_start
        self.mod.frame_end = self.frame_end

        if self.is_start:
            self.mod.frame_start = x
        else:
            self.mod.frame_end = x
        return {'FINISHED'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_region_x
            self.execute(context)
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.mod.frame_start = self.frame_start
            self.mod.frame_end = self.frame_end
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_mouse_x = event.mouse_region_x
        self.is_start = True
        fcurve = context.active_editable_fcurve
        x, y = context.region.view2d.region_to_view(pie_menu_context.mouse_region_x, pie_menu_context.mouse_region_y)

        mod = select_current_mod(fcurve, context)

        if mod is None:
            return {'CANCELLED'}

        self.is_start = select_side(mod, x)

        self.mod = mod
        self.frame_start = self.mod.frame_start
        self.frame_end = self.mod.frame_end

        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class ZENU_OT_anim_noise_move(bpy.types.Operator):
    bl_label = 'Noise Move'
    bl_idname = 'zenu.anim_noise_move'
    bl_options = {'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    mod: bpy.types.FModifierNoise
    is_start: bool = True
    init_mouse_x: int = 0
    mouse_x: int = 0
    frame_start: float = 0
    frame_end: float = 0

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll(context)

    def execute(self, context: bpy.types.Context):
        x, y = context.region.view2d.region_to_view(self.mouse_x, 0)
        rel = self.init_mouse_x - x
        self.mod.frame_start = self.frame_start - rel
        self.mod.frame_end = self.frame_end - rel
        return {'FINISHED'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_region_x
            self.execute(context)
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.mod.frame_start = self.frame_start
            self.mod.frame_end = self.frame_end
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.is_start = True
        self.init_mouse_x, y = context.region.view2d.region_to_view(event.mouse_region_x, 0)
        fcurve = context.active_editable_fcurve
        x, y = context.region.view2d.region_to_view(pie_menu_context.mouse_region_x, pie_menu_context.mouse_region_y)

        mod = select_current_mod(fcurve, context)

        if mod is None:
            return {'CANCELLED'}

        self.is_start = select_side(mod, x)

        self.mod = mod
        self.frame_start = self.mod.frame_start
        self.frame_end = self.mod.frame_end

        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class ZENU_OT_anim_noise_remove(bpy.types.Operator):
    bl_label = 'Noise Remove'
    bl_idname = 'zenu.anim_noise_remove'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll(context)

    def execute(self, context: bpy.types.Context):
        fcurve = context.active_editable_fcurve
        mod = select_current_mod(fcurve, context)

        if mod is None:
            return {'CANCELLED'}

        fcurve.modifiers.remove(mod)
        fcurve.update()
        update_window(True)
        return {'FINISHED'}


classes = (
    ZENU_OT_anim_noise,
    ZENU_OT_anim_noise_blend,
    ZENU_OT_anim_noise_edit,
    ZENU_OT_anim_noise_remove,
    ZENU_OT_anim_noise_move,
    ZENU_OT_anim_noise_property_edit,
    ZENU_PT_mod_panel
)

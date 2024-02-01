import bpy
from ...utils import check_mods

active_curve = None


class ZENU_OT_edger(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    bl_label = 'Edges To Curve'
    bl_idname = 'zenu.edger'
    curve_data: bpy.types.Curve
    start_mouse = 0

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return check_mods('e')

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        name = obj.name
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate()

        split = [i for i in context.selected_objects if i.name != name][0]

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        split.select_set(True)
        context.view_layer.objects.active = split
        bpy.ops.object.convert(target='CURVE')

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        global active_curve
        active_curve = split

        return {'FINISHED'}

    def modal(self, context, event):
        speed = 8000 if event.shift else 1000

        if active_curve is None:
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE':
            active_curve.data.bevel_depth = (abs((event.mouse_x + event.mouse_y) - self.start_mouse)) / speed
        elif event.type == 'LEFTMOUSE':  # Confirm
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            bpy.data.objects.remove(active_curve)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.start_mouse = event.mouse_x + event.mouse_y
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

import bpy
from ....base_panel import BasePanel
from . import nla_loops, nla_separate, clear_animation
from ....utils import register_modules, unregister_modules

class ZENU_OT_animated_time_add_driver(bpy.types.Operator):
    bl_label = 'Add Driver'
    bl_idname = 'zenu.animated_time_add_driver'
    remove: bpy.props.BoolProperty()

    def execute(self, context: bpy.types.Context):
        nla_strip = context.active_nla_strip

        if self.remove:
            fcurve = nla_strip.driver_remove('strip_time')
            return {'FINISHED'}

        fcurve = nla_strip.driver_add('strip_time')
        fcurve.driver.type = 'SUM'
        fcurve.driver.variables.new()
        return {'FINISHED'}


class ZENU_PT_animation_nla_strip_time(BasePanel):
    bl_label = 'Animation Strip Time'
    bl_space_type = 'NLA_EDITOR'

    def draw_nla(self, nla_strip: bpy.types.NlaStrip):
        layout = self.layout.box()
        layout.label(text=nla_strip.name)
        time = (nla_strip.frame_end - nla_strip.frame_start) / bpy.context.scene.render.fps
        layout.label(text=f'{time}')

        col = layout.column(align=True)
        col.scale_y = 1.5

        col.prop(nla_strip, 'use_animated_time', icon='MODIFIER')
        col.prop(nla_strip, 'use_animated_time_cyclic', icon='MODIFIER')
        col.prop(nla_strip, 'use_sync_length', icon='MODIFIER')
        col.prop(nla_strip, 'strip_time')
        col.prop(nla_strip, 'repeat')

        col = layout.column(align=True)
        col.scale_y = 1.5
        col.prop(nla_strip, 'blend_in')
        col.prop(nla_strip, 'blend_out')


    def draw(self, context: bpy.types.Context):
        layout = self.layout
        nla_strips = context.selected_nla_strips

        for nla_strip in nla_strips:
            # print()
            self.draw_nla(nla_strip)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_animation_nla_strip_time,
    ZENU_OT_animated_time_add_driver,
))

modules = (
    nla_loops,
    nla_separate,
    clear_animation
)

def register():
    reg()
    register_modules(modules)


def unregister():
    unreg()
    unregister_modules(modules)

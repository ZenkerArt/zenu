import bpy
from .operators import ZENU_OT_trigger_action, ZENU_OT_calculate_triggers, ZENU_OT_calculate_triggers_realtime, \
    ZENU_OT_calculate_triggers_realtime_clipboard, ZENU_OT_pasts_videos_from_clipboard, ZENU_random_audio_import
from .utils import get_active_point, get_active_trigger
from ...base_panel import BasePanel


class ZENU_UL_triggers_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item
        layout.prop(slot, 'name', text='', emboss=False)


class ZENU_PT_audio_gen(BasePanel):
    bl_label = 'Audio Gen'

    def audio_triggers(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column(align=True)
        col.template_list('ZENU_UL_triggers_list', '', context.scene, 'zenu_at', context.scene,
                          'zenu_at_active')

        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Add')
        op.action = 'ADD'
        op.type = 'TRIGGER'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Remove')
        op.action = 'REMOVE'
        op.type = 'TRIGGER'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Clear')
        op.action = 'CLEAR'
        op.type = 'TRIGGER'

        col = layout.column(align=True)
        item = get_active_trigger()

        if item is None:
            return

        col.prop(item, 'obj')
        col.prop(item, 'path')

    def audio_triggers_point(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column(align=True)
        col.template_list('ZENU_UL_triggers_list', '', context.scene, 'zenu_at_point', context.scene,
                          'zenu_at_point_active')
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Add')
        op.action = 'ADD'
        op.type = 'POINT'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Remove')
        op.action = 'REMOVE'
        op.type = 'POINT'
        op = col.operator(ZENU_OT_trigger_action.bl_idname, text='Clear')
        op.action = 'CLEAR'
        op.type = 'POINT'

        col = layout.column(align=True)
        item = get_active_point()

        if item is None:
            return

        col.prop(item, 'obj')

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        self.audio_triggers(context)

        layout.label(text='Trigger Pointsт')
        self.audio_triggers_point(context)

        layout.operator(ZENU_OT_calculate_triggers.bl_idname)
        layout.operator(ZENU_OT_calculate_triggers_realtime.bl_idname)
        layout.operator(ZENU_OT_calculate_triggers_realtime_clipboard.bl_idname)
        layout.operator(ZENU_OT_pasts_videos_from_clipboard.bl_idname)
        layout.operator(ZENU_random_audio_import.bl_idname)


classes = (
    ZENU_UL_triggers_list,
    ZENU_PT_audio_gen
)

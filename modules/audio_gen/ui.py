import bpy
from .cache_operators import ZENU_OT_pasts_videos_from_clipboard, ZENU_OT_calculate_triggers_realtime_cache, \
    ZENU_OT_pasts_audio_from_clipboard
from .operators import ZENU_OT_trigger_action, ZENU_OT_calculate_triggers, ZENU_OT_calculate_triggers_realtime, \
    ZENU_OT_calculate_triggers_realtime_clipboard, ZENU_random_audio_import
from .utils import get_active_trigger
from ...base_panel import BasePanel


class ZENU_UL_triggers_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item
        layout.prop(slot, 'name', text='', emboss=False)


class ZENU_UL_trigger_cache_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item
        layout.prop(slot, 'name', text='', emboss=False)


class ZENU_PT_audio_gen(BasePanel):
    bl_label = 'Audio Gen'

    @staticmethod
    def draw_list(layout: bpy.types.UILayout, typ: str, collection: str, index: str):
        context = bpy.context
        row = layout.row()

        row.template_list('ZENU_UL_triggers_list', '', context.scene, collection, context.scene, index, rows=3)

        col = row.column(align=True)

        op = col.operator(ZENU_OT_trigger_action.bl_idname, icon='ADD', text='')
        op.action = 'ADD'
        op.type = typ
        op = col.operator(ZENU_OT_trigger_action.bl_idname, icon='REMOVE', text='')
        op.action = 'REMOVE'
        op.type = typ
        col.separator()
        op = col.operator(ZENU_OT_trigger_action.bl_idname, icon='TRASH', text='')
        op.action = 'CLEAR'
        op.type = typ

    def audio_triggers(self, context: bpy.types.Context):
        layout = self.layout

        self.draw_list(layout, 'TRIGGER', 'zenu_at', 'zenu_at_active')

        col = layout.column(align=True)
        item = get_active_trigger()

        if item is None:
            return
        #
        # col.prop(item, 'obj')
        col.prop(item, 'path')

    def audio_triggers_point(self, context: bpy.types.Context):
        layout = self.layout

        self.draw_list(layout, 'POINT', 'zenu_at_point', 'zenu_at_point_active')

        # col = layout.column(align=True)
        # item = get_active_point()
        #
        # if item is None:
        #     return
        #
        # col.prop(item, 'obj')

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        self.audio_triggers(context)

        layout.label(text='Trigger Points')
        self.audio_triggers_point(context)

        layout.operator(ZENU_OT_calculate_triggers.bl_idname)
        layout.operator(ZENU_OT_calculate_triggers_realtime.bl_idname)

        layout.template_list('ZENU_UL_trigger_cache_list', '', context.scene, 'zenu_trigger_cache', context.scene,
                             'zenu_trigger_cache_active', rows=3)

        header, panel = layout.panel('utils', default_closed=True)
        header.label(text="Utils")

        if panel:
            panel.operator(ZENU_OT_pasts_videos_from_clipboard.bl_idname)
            panel.operator(ZENU_OT_pasts_audio_from_clipboard.bl_idname)
            panel.operator(ZENU_OT_calculate_triggers_realtime_cache.bl_idname)
            panel.operator(ZENU_random_audio_import.bl_idname)
            panel.operator(ZENU_OT_calculate_triggers_realtime_clipboard.bl_idname)


classes = (
    ZENU_UL_triggers_list,
    ZENU_UL_trigger_cache_list,
    ZENU_PT_audio_gen
)

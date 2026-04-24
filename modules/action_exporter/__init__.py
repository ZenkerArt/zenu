import bpy
from .trigger_export_ops import ActionExportTriggerOps
from .action_list_export import action_list_export
from .export_ops import ActionExportOps
from ...base_panel import BasePanel


class ZENU_PT_action_export(BasePanel):
    bl_label = 'Action Export'
    bl_context = ''

    def get_action_slot(self, obj: bpy.types.Object, action: bpy.types.Action):
        if obj.animation_data is None:
            return None

        if obj.animation_data.action != action:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action == action:
                        return strip.action_slot
        else:
            return obj.animation_data.action_slot

        return None
    def get_action_nla(self, obj: bpy.types.Object, action: bpy.types.Action):
        if obj.animation_data is None:
            return None

        if obj.animation_data.action != action:
            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action == action:
                        return strip
        else:
            return obj.animation_data.action_blend_type

        return None

    def draw_export_settings(self, layout: bpy.types.UILayout):
        active_item = action_list_export.active

        header, lay = layout.panel('Settings', default_closed=True)
        header.label(text='Settings')

        if not lay:
            return

        box = lay.box()
        box.label(text='Mesh')
        row = box.grid_flow(columns=2, align=True)
        row.scale_y = 1.2
        row.prop(active_item, 'export_mesh',
                 text='Export Mesh', icon='MESH_CUBE')
        row.prop(active_item, 'apply_mods',
                 text='Apply Modifier', icon='MODIFIER')
        row.prop(active_item, 'export_textures',
                 text='Export Textures', icon='TEXTURE')
        
        row.prop(active_item, 'use_bake_only_animated',
            text='Only Animated', icon='ANIM_DATA')
        
        lay.prop(active_item, 'export_animinfo',
                 text='Export AnimInfo', icon='ANIM_DATA')



        col = lay.column(align=True)
        col.prop(active_item, 'use_additive',
                 text='Additive', icon='ADD')
        if active_item.use_additive:
            col.prop(active_item, 'action_additive',
                     text='', icon='ACTION')
            

        lay.prop(active_item, 'export_path',
                 text='', icon='EXPORT')

    def draw_trigger(self, layout: bpy.types.UILayout):
        active_item = action_list_export.active

        header, lay = layout.panel('Trigger', default_closed=True)
        header.label(text='Trigger')

        if not lay:
            return

        lay.label(text=active_item.trigger_data)
        lay.label(text=f'{active_item.trigger_edit_mode}')
        if active_item.trigger_edit_mode:
            op = ActionExportTriggerOps.draw_action(
                lay, ActionExportTriggerOps.action_end_editing, text='End Edit', depress=True)
        else:
            op = ActionExportTriggerOps.draw_action(
                lay, ActionExportTriggerOps.action_start_editing, text='Edit')

        op.item_uuid = active_item.uuid

        op = ActionExportTriggerOps.draw_action(
            lay, ActionExportTriggerOps.action_export, text='Export')

        op.item_uuid = active_item.uuid

        if active_item.trigger_edit_mode:
            for marker in bpy.context.scene.timeline_markers:
                box = lay.box()
                box.label(text=f'Frame {marker.frame}')

                col = box.column(align=True)
                row = col.row(align=True)
                op = ActionExportTriggerOps.draw_action(
                    row, ActionExportTriggerOps.action_remove, text='', icon='REMOVE')
                row.prop(marker, 'name', text='')
                col.prop(marker, 'frame', text='')
                op.name = marker.name
                op.frame = marker.frame

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        action_list_export.draw_ui(layout)
        active_item = action_list_export.active

        if active_item is None:
            return

        layout.label(text=active_item.data)
        col = layout.column(align=True)
        col.prop(active_item, 'action', text='')
        op = ActionExportOps.draw_action(
            col, ActionExportOps.action_export, text='Export')
        op.item_uuid = active_item.uuid
        
        op = ActionExportOps.draw_action(
            col, ActionExportOps.action_bake_only_animated, text='Bake')
        col.scale_y = 1.5

        op.item_uuid = active_item.uuid

        self.draw_export_settings(layout)
        self.draw_trigger(layout)

        action: bpy.types.Action = active_item.action
        data = active_item.load_anim_info()

        col = layout.column()
        
        for name, obj_data in data.objects.items():
            box = col.box()
            row = box.row(align=True)
            row.scale_y = 1.4
            row.label(text=name)
            row.alert = True
            obj = bpy.data.objects.get(name)
            
            remove_text = ''
            if obj is None:
                remove_text = 'Object removed'
            
            
            op = ActionExportOps.draw_action(
                row, ActionExportOps.action_toggle, text=remove_text, icon='REMOVE')
            op.name = name
            
            try:
                box.box().label(
                    text=f'{obj_data.slot}')
            except AttributeError:
                pass


        for obj in bpy.data.objects:
            has_obj = data.has_object(obj.name)
            action_slot = self.get_action_slot(obj, action)

            if has_obj or not action_slot:
                continue

            box = col.box()
            row = box.row(align=True)
            row.scale_y = 1.4
            row.label(text=obj.name)
            row.alert = has_obj

            op = ActionExportOps.draw_action(
                row, ActionExportOps.action_toggle, text='', icon='ADD')
            op.name = obj.name
            op.slot = action_slot.name_display


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_action_export,
    ActionExportOps.gen_op(),
    ActionExportTriggerOps.gen_op()
))


def register():
    action_list_export.register()
    reg()


def unregister():
    action_list_export.unregister()
    unreg()

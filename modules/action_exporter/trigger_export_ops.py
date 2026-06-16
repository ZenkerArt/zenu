import bpy

from ..base_operator.action_operator import ActionOperator

from .utils import export_animinfo
from .action_list_export import action_list_export

class ActionExportTriggerOps(ActionOperator):
    bl_label = 'Action Export'
    item_uuid: bpy.props.StringProperty()
    frame: bpy.props.IntProperty()
    name: bpy.props.StringProperty()

    def action_start_editing(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)
        trigger_data = item.load_triggers()
        item.trigger_edit_mode = True

        bpy.context.scene.timeline_markers.clear()

        trigger_data.load_markers()

    def action_end_editing(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)
        trigger_data = item.load_triggers()
        item.trigger_edit_mode = False

        trigger_data.save_markers()
        bpy.context.scene.timeline_markers.clear()
        item.trigger_data = trigger_data.to_dict()

    def action_remove(self, context: bpy.types.Context):
        for marker in bpy.context.scene.timeline_markers:
            if self.frame == marker.frame and self.name == marker.name:
                bpy.context.scene.timeline_markers.remove(marker)

    def action_export(self, context: bpy.types.Context):
        item = action_list_export.get_by_id(self.item_uuid)
        filepath = export_animinfo(item)

        self.report({'INFO'}, f'Exported to {filepath}')
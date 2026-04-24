import uuid

# from .draw_item import draw

from ..base_ui_list import ZenuUIList
from .models import ActionExportItem, ActionExport


class ActionExportList(ZenuUIList[ActionExport]):
    name = 'action_export_list'
    _property_group = ActionExport

    def _draw(self, layout, item: ActionExport):
        layout.prop(item, 'name', text='', emboss=False)
        row = layout.row(align=True)

        if item.export_mesh:
            row.label(icon='MESH_CUBE')
        if item.export_textures:
            row.label(icon='TEXTURE')

        # draw(item)
        # op = ActionExportOps.draw_action(
        #     layout, ActionExportOps.action_export, text='', icon='EXPORT', emboss=False)
        # op.item_uuid = item.uuid

    def get_by_id(self, uuid: str):
        for i in self.prop_list:
            if i.uuid == uuid:
                return i

        return

    def add(self):
        item = super().add()
        item.name = 'No Name'
        item.uuid = uuid.uuid4().hex
        item.data = ActionExportItem().to_json()
        return item


action_list_export = ActionExportList()
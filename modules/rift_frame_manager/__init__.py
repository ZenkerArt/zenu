import bpy

from ..base_ui_list import ZenuUIList
from ...base_panel import RiftBasePanel


class RiftFrameAction(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Name')
    action: bpy.props.PointerProperty(type=bpy.types.Action)


class RiftFrameList(ZenuUIList[RiftFrameAction]):
    name = 'rift_frame_manager'
    _property_group = RiftFrameAction

    def _draw(self, layout: bpy.types.UILayout, item: RiftFrameAction):
        layout.label(text=item.action.name if item.action else (item.name or 'Empty'))

    def add(self) -> RiftFrameAction:
        item = super().add()
        item.name = 'Name'
        return item

    def _on_select(self):
        item = self.active
        obj = bpy.context.active_object
        if item is None or item.action is None or obj is None:
            return

        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = item.action


rift_frame_list = RiftFrameList()


class ZENU_PT_rift_frame_manager(RiftBasePanel):
    bl_label = 'Frame Manager'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        rift_frame_list.draw_ui(layout=layout)

        item = rift_frame_list.active
        if item is None:
            return

        col = layout.column(align=True)
        col.prop(item, 'name', text='')
        col.prop(item, 'action', text='')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_rift_frame_manager,
))


def register():
    reg()
    rift_frame_list.register()


def unregister():
    unreg()
    rift_frame_list.unregister()

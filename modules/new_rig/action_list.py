from ..base_ui_list import ZenuUIList
import bpy


class RigActionListItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    bone: bpy.props.StringProperty()
    mirror_bone: bpy.props.StringProperty()
    mirror: bpy.props.BoolProperty()
    action: bpy.props.PointerProperty(type=bpy.types.Action)


class RigActionList(ZenuUIList[RigActionListItem]):
    name = 'rig_action_list'
    _property_group = RigActionListItem

    def _draw(self, layout, item):
        layout.prop(item, 'name', text='', emboss=False)

    def add(self):
        item = super().add()
        item.name = 'No Name'
        return item

    def _on_select(self):
        pass


rig_action_list = RigActionList()

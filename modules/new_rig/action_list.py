from ast import Return
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
    _active_path = bpy.types.Object
    _property_group = RigActionListItem

    def _draw(self, layout, item):
        layout.prop(item, 'name', text='', emboss=False)

    def add(self):
        item = super().add()
        item.name = 'No Name'
        return item
    
    def get_obj(self):
        rig_settings = bpy.context.active_object.zenu_rig_props
        
        rig_type: str = rig_settings.rig_type
        link_rig: bpy.types.Object = rig_settings.link_rig
        if rig_type == 'GENERATED':
            return link_rig
        
        return super().get_obj()

    def _on_select(self):
        pass



rig_action_list = RigActionList()

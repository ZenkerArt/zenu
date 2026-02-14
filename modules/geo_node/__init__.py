from dataclasses import dataclass
import json
import bpy

from ..base_ui_list import ZenuUIList
from ...base_panel import BasePanel
from ..base_operator import action_operator


@dataclass
class GeoModPath:
    obj_name: str

    @property
    def obj(self) -> bpy.types.Object:
        return bpy.data.objects[self.obj_name]


class GeoNodeBakeProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    geo_nodes: bpy.props.StringProperty()


class GeoNodeBakeList(ZenuUIList[GeoNodeBakeProperty]):
    name = 'geo_node_baker_list'
    _property_group = GeoNodeBakeProperty

    @staticmethod
    def _get_json(data: GeoNodeBakeProperty) -> dict[str, any]:
        try:
            return json.loads(data.geo_nodes)
        except Exception:
            return {'objects': {}}

    def _get_active_objects(self) -> dict[str, any]:
        return self._get_json(self.active)['objects']

    def _save_active_objects(self, objects: dict[str, any]):
        data = self._get_json(self.active)
        data['objects'] = objects

        self.active.geo_nodes = json.dumps(data)

    def _draw(self, layout, item):
        layout.prop(item, 'name', text='', emboss=False)

    def add(self):
        item = super().add()
        item.name = 'No Name'
        item.geo_nodes = json.dumps(self._get_json(item))
        return item

    def add_mod(self, obj_name: str):
        data = self._get_active_objects()
        data[obj_name] = {
            'obj_name': obj_name,
        }

        self._save_active_objects(data)

    def remove_mod(self, obj_name: str):
        data = self._get_active_objects()
        del data[obj_name]

        self._save_active_objects(data)

    def get_mods(self) -> list[GeoModPath]:
        lst = []
        for i in self._get_active_objects().values():
            lst.append(GeoModPath(**i))

        return lst

    def exists(self, name: str):
        return self._get_active_objects().get(name) is not None

    def _on_select(self):
        pass


geo_node_baker_list = GeoNodeBakeList()


class GeoNodeBakerActions(action_operator.ActionOperator):
    bl_label = 'Geo Node Baker Actions'
    obj_name: bpy.props.StringProperty()
    disable: bpy.props.BoolProperty()

    def action_add(self, context: bpy.types.Context):
        geo_node_baker_list.add_mod(self.obj_name)

    def action_remove(self, context: bpy.types.Context):
        geo_node_baker_list.remove_mod(self.obj_name)

    def action_select(self, context: bpy.types.Context):
        bpy.ops.object.select_all(action='DESELECT')

        for i in geo_node_baker_list.get_mods():
            i.obj.select_set(True)

    def action_disable_mod(self, context: bpy.types.Context):
        for i in geo_node_baker_list.get_mods():
            
            for mod in i.obj.modifiers:
                mod: bpy.types.NodesModifier
                if not isinstance(mod, bpy.types.NodesModifier):
                    continue

                mod.show_viewport = self.disable
            

class ZENU_PT_geo_node(BasePanel):
    bl_label = 'Geo Node'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object

        geo_node_baker_list.draw_ui(layout)

        col = layout.box().column()
        for i in geo_node_baker_list.get_mods():
            row = col.box().row()
            name = i.obj_name
            row.label(text=name)

            op = GeoNodeBakerActions.draw_action(
                row, GeoNodeBakerActions.action_remove, text='', icon='REMOVE')
            op.obj_name = name
            
        col = col.column(align=True)
        op = GeoNodeBakerActions.draw_action(
            col, GeoNodeBakerActions.action_select)

        row = col.row(align=True)
        op = row.operator('object.simulation_nodes_cache_bake', text='Bake')
        op.selected = True
        op = row.operator('object.simulation_nodes_cache_delete', text='Remove')
        op.selected = True
        
        col = col.column()
        col.separator()
        col = col.row(align=True)
        
        op = GeoNodeBakerActions.draw_action(
                col, GeoNodeBakerActions.action_disable_mod, text='Show')
        op.disable = True
        op = GeoNodeBakerActions.draw_action(
                col, GeoNodeBakerActions.action_disable_mod, text='Hide')
        op.disable = False
        
        if obj is None:
            return

        col = layout.box().column()
        for mod in context.selected_objects:
            name = mod.name
            if geo_node_baker_list.exists(name):
                continue

            row = col.box().row()
            row.label(text=name)

            op = GeoNodeBakerActions.draw_action(
                row, GeoNodeBakerActions.action_add, text='', icon='ADD')
            op.obj_name = name


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_geo_node,
    GeoNodeBakerActions.gen_op(),
))


def register():
    reg()
    geo_node_baker_list.register()


def unregister():
    unreg()
    geo_node_baker_list.unregister()

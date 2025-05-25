import json

import bpy
from .pie_panel import PiePanel
from ...keybindings import view_3d, dopesheet, graph_editor, sequence_editor
from ...package_name import package_name


def create_layout(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    actions_layout = layout.column(align=True)
    actions_layout.scale_x = 1.5
    actions_layout.scale_y = 1.5
    return actions_layout


class Panels:
    _panels: dict[str, PiePanel]

    def __init__(self):
        self.clear()

    def clear(self):
        self._panels = {}

    def add_panel(self, id: str):
        self._panels[id] = PiePanel(id)
        return self._panels[id]

    def from_dict(self, dct: str):
        id = dct['id']
        self._panels[id] = PiePanel(id).from_dict(dct)

    def get_by_name(self, name: str):
        return self._panels.get(name)

    @property
    def children(self):
        return self._panels


panels = Panels()


class ZENU_MT_context_new(bpy.types.Menu):
    bl_label = 'Zenu Context New'
    bl_idname = 'ZENU_MT_context_new'

    def draw(self, context: bpy.types.Context):
        obj = context.active_object
        layout = self.layout
        pie = layout.menu_pie()
        modifiers_layout = create_layout(pie)
        right_l = create_layout(pie)  # PiePanel(pie, 'right')
        properties_layout = create_layout(pie)

        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.scale_y = 7
        other_menu = other.column(align=True)
        other_menu.scale_y = 1.5

        data = context.preferences.addons[package_name].preferences.pie_menu

        # pie_menu = json.loads(data)

        for _, item in panels.children.items():
            item.draw(right_l)


class ZENU_OT_open_context_pie_new(bpy.types.Operator):
    bl_label = 'Context Pie'
    bl_idname = 'zenu.open_context_pie_new'

    def execute(self, context: bpy.types.Context):
        bpy.ops.wm.call_menu_pie(name=ZENU_MT_context_new.bl_idname)
        return {'FINISHED'}


class ZENU_OT_edit_menu(bpy.types.Operator):
    bl_label = 'Edit Menu'
    bl_idname = 'zenu.edit_menu'

    id: bpy.props.StringProperty()
    op: bpy.props.StringProperty()
    text: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        data = json.loads(context.preferences.addons[package_name].preferences.pie_menu)
        item = None
        for i in data['menus']:
            if i['id'] == self.id:
                item = i
                break

        if item:
            item['op'] = self.op
            item['text'] = self.text
            context.preferences.addons[package_name].preferences.pie_menu = json.dumps(data)
        return {'FINISHED'}

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, 'op')
        layout.prop(self, 'text')

    def invoke(self, context, event):
        data = json.loads(context.preferences.addons[package_name].preferences.pie_menu)
        item = None
        for i in data['menus']:
            if i['id'] == self.id:
                item = i
                break

        if item:
            self.op = item['op']
            self.text = item['text']
        return context.window_manager.invoke_props_dialog(self)


class ZENU_OT_add_item(bpy.types.Operator):
    bl_label = 'Add Item'
    bl_idname = 'zenu.add_item'

    id: bpy.props.StringProperty()
    op: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        # print(eval(context.scene.context_operator))
        layout.prop(context.scene, 'context_operator')
        # bpy.ops.mesh.primitive_cube_add

        op = context.window_manager.operator_properties_last("MESH_OT_primitive_cube_add")
        props = list(filter(lambda x: not ('__' in x or 'rna_' in x or 'bl_rna' in x), dir(op)))

        for prop in props:
            layout.prop(op, prop)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ZENU_OT_select_panel(bpy.types.Operator):
    bl_label = 'Select Panel'
    bl_idname = 'zenu.select_panel'
    panel_id: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        context.scene.context_active_panel = self.panel_id
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_open_context_pie_new,
    ZENU_OT_edit_menu,
    ZENU_OT_add_item,
    ZENU_OT_select_panel,
    ZENU_MT_context_new
))


def register():
    reg()
    bpy.types.Scene.context_operator = bpy.props.StringProperty()

    bpy.types.Scene.context_pie_string_input = bpy.props.StringProperty()
    bpy.types.Scene.context_active_panel = bpy.props.StringProperty()

    view_3d.new(ZENU_OT_open_context_pie_new.bl_idname, type='W', ctrl=True)
    dopesheet.new(ZENU_OT_open_context_pie_new.bl_idname, type='W', ctrl=True)
    graph_editor.new(ZENU_OT_open_context_pie_new.bl_idname, type='W', ctrl=True)
    sequence_editor.new(ZENU_OT_open_context_pie_new.bl_idname, type='W', ctrl=True)
    panels.clear()
    panels.add_panel('Left')
    panels.from_dict({'id': 'right', 'data': {
        'object.convert':
            {'class_name': 'OperatorItem', 'path': 'object.convert', 'text': '', 'icon': None},
        'object.shade_smooth':
            {'class_name': 'OperatorItem', 'path': 'object.shade_smooth', 'text': '', 'icon': None}}})


def unregister():
    unreg()


def addon_panel(cls, layout: bpy.types.UILayout):
    context = bpy.context
    box = layout.box()

    row = box.row(align=True)
    for key, value in panels.children.items():
        op = row.operator(ZENU_OT_select_panel.bl_idname, text=key.title(),
                          depress=context.scene.context_active_panel == key)
        op.panel_id = key

    panel = panels.get_by_name(context.scene.context_active_panel)

    if panel is None:
        return

    panel_ui = layout.box().column(align=True)
    for operator in panel.operators:
        panel_ui.operator(operator.path)

    layout.operator(ZENU_OT_add_item.bl_idname)

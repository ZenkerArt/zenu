import inspect
import random
import sys
from typing import Set
from uuid import uuid4

import bpy

from ...base_panel import BasePanel
from ...utils import update_window
from bpy.types import NodeTree, NodeSocket



def socket_type_names() -> Set[str]:
    names = set()
    for name, member in inspect.getmembers(sys.modules[__name__]):
        is_module_cls = inspect.isclass(member) and member.__module__ == __name__
        if is_module_cls:
            if NodeSocket in member.__bases__:
                names.add(member.bl_idname)
    return names


class VertexLayer(bpy.types.PropertyGroup):
    uid: bpy.props.StringProperty()
    parent_uid: bpy.props.StringProperty()
    index: bpy.props.IntProperty()
    order: bpy.props.IntProperty()

    name: bpy.props.StringProperty()
    is_folder: bpy.props.BoolProperty()
    vertex_color: bpy.props.StringProperty()
    color: bpy.props.FloatVectorProperty()


def sort_vertex_layers(obj: bpy.types.Object):
    folders = {item.uid: item for item in obj.zenu_vertex_layer}  # if item.is_folder

    def get_weight(item: VertexLayer):
        if item.is_folder:
            return item.index
        return folders[item.parent_uid].index - item.index

    n = len(obj.zenu_vertex_layer)
    for i in range(n):
        for j in range(0, n - i - 1):
            item1 = obj.zenu_vertex_layer[j]
            item2 = obj.zenu_vertex_layer[j + 1]

            value1 = get_weight(item1)
            value2 = get_weight(item2)

            if value2 > value1:
                obj.zenu_vertex_layer.move(j, j + 1)

    generate_shader(obj)


def get_active_layer(obj: bpy.types.Object) -> VertexLayer | None:
    try:
        return obj.zenu_vertex_layer[obj.zenu_vertex_layer_active]
    except IndexError:
        return None


def get_layers(obj: bpy.types.Object) -> list[VertexLayer]:
    for index, item in enumerate(obj.zenu_vertex_layer):
        item.order = index

    return list(obj.zenu_vertex_layer)


def get_folders(obj: bpy.types.Object):
    return [i for i in get_layers(obj) if i.is_folder]


def get_folder_layers(obj: bpy.types.Object, folder: VertexLayer) -> list[VertexLayer]:
    layers = []

    if not folder.is_folder:
        return layers

    for layer in get_layers(obj):
        if layer.is_folder:
            continue

        if layer.parent_uid == folder.uid:
            layers.append(layer)

    return layers


def remove_layer(obj: bpy.types.Object, layer: VertexLayer):
    value = False
    uid = layer.uid
    if layer.is_folder:
        return False

    for index, lay in enumerate(get_layers(obj)):
        if lay.uid == uid:
            obj.zenu_vertex_layer.remove(index)
            value = True
            break

    shader = get_shader(obj)
    frame_name = get_frame(uid)

    for i in shader.nodes:
        if i.parent and i.parent.name == frame_name:
            shader.nodes.remove(i)

    shader.nodes.remove(shader.nodes.get(frame_name))

    return value


def remove_bulk_layer(obj: bpy.types.Object, layers: list[VertexLayer]):
    layers_uid = [layer.uid for layer in layers]

    for uid in layers_uid:
        for layer in get_layers(obj):
            if uid == layer.uid:
                obj.zenu_vertex_layer.remove(layer.order)

    shader = get_shader(obj)

    frames = [get_frame(uid) for uid in layers_uid]

    for i in shader.nodes:
        if i.parent and i.parent.name in frames:
            print(i.parent.name)
            # shader.nodes.remove(i)

    return False


def get_shader(obj: bpy.types.Object):
    name = f'[VertexLayers]{obj.name}'
    vertex_layers = bpy.data.node_groups.get(name)
    if vertex_layers is None:
        vertex_layers = bpy.data.node_groups.new(name, 'ShaderNodeTree')

    return vertex_layers


def get_frame(uid: str):
    return f'[Frame]{uid}'


def generate_shader(obj: bpy.types.Object):
    vertex_layers = get_shader(obj)

    # vertex_layers.nodes.clear()

    sockets = vertex_layers.interface.items_tree.keys()

    def get_or_create(name: str, type: str):
        node = vertex_layers.nodes.get(name)
        if node is None:
            node = vertex_layers.nodes.new(type)
            node.name = name

        return node

    group_outputs = get_or_create('Output', 'NodeGroupOutput')
    group_outputs.location = (0, 0)

    for y, folder in enumerate(get_folders(obj)):
        if folder.name in sockets:
            socket = vertex_layers.interface.items_tree.get(folder.name)
        else:
            socket = vertex_layers.interface.new_socket(folder.name, description=folder.uid, in_out='OUTPUT',
                                                        socket_type='NodeSocketColor')

        folder_frame: bpy.types.NodeFrame = get_or_create(get_frame(folder.uid), 'NodeFrame')
        folder_frame.label = folder.name
        folder_frame.location = (0, 0)

        prev_mix = None
        folder_layers = get_folder_layers(obj, folder)
        layers_len = len(folder_layers)
        folder_layers.reverse()
        for x, layer in enumerate(folder_layers, 1):
            layer_frame: bpy.types.NodeFrame = get_or_create(get_frame(layer.uid), 'NodeFrame')
            layer_frame.label = layer.name
            layer_frame.location = (0, 0)
            layer_frame.parent = folder_frame
            layer_frame.use_custom_color = True
            layer_frame.color = (0.608, 0.03546, 0)

            node_x = -225 * x
            node_y = -500 * y

            mix = get_or_create(layer.uid, 'ShaderNodeMix')
            mix.data_type = 'RGBA'
            mix.blend_type = 'MIX'
            mix.label = f'[Mix]{layer.name}'
            mix.location = (node_x, node_y)

            attribute = get_or_create(f'[Attr]{layer.uid}', 'ShaderNodeAttribute')
            attribute.attribute_name = layer.uid
            attribute.label = layer.name
            attribute.location = (node_x, node_y + 200)

            # vertex_layers.links.new(mix.inputs[6], attribute.outputs[0])
            vertex_layers.links.new(mix.inputs[0], attribute.outputs[2])

            if prev_mix:
                vertex_layers.links.new(mix.outputs[2], prev_mix.inputs[6])

            if x == 1:
                vertex_layers.links.new(mix.outputs[2], group_outputs.inputs[socket.index])

            if x == layers_len:
                value = get_or_create(folder.uid, 'ShaderNodeRGB')
                value.location = (node_x - 200, node_y)
                value.label = folder.name
                value.outputs[0].default_value = (1, 1, 1, 1)
                vertex_layers.links.new(mix.inputs[6], value.outputs[0])
                value.parent = folder_frame

            prev_mix = mix
            mix.parent = layer_frame
            attribute.parent = layer_frame


class ZENU_OT_move_vertex_layer(bpy.types.Operator):
    bl_label = 'Move Vertex Layer'
    bl_idname = 'zenu.move_vertex_layer'

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        index = obj.zenu_vertex_layer_active

        move = index + 1

        obj.zenu_vertex_layer.move(index, move)
        obj.zenu_vertex_layer_active = move
        return {'FINISHED'}


class ZENU_OT_clear_vertex_layer(bpy.types.Operator):
    bl_label = 'Clear Vertex Layer'
    bl_idname = 'zenu.clear_vertex_layer'

    def execute(self, context: bpy.types.Context):
        context.active_object.zenu_vertex_layer.clear()
        return {'FINISHED'}


class ZENU_OT_sort_vertex_layer(bpy.types.Operator):
    bl_label = 'Sort Vertex Layer'
    bl_idname = 'zenu.sort_vertex_layer'

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        sort_vertex_layers(obj)
        return {'FINISHED'}


class ZENU_OT_random_vertex_layer(bpy.types.Operator):
    bl_label = 'Random Vertex Layer'
    bl_idname = 'zenu.random_vertex_layer'

    def execute(self, context: bpy.types.Context):
        obj = context.active_object

        end = len(obj.zenu_vertex_layer)

        for index in range(0, end):
            obj.zenu_vertex_layer.move(index, random.randint(0, end))

        return {'FINISHED'}


class ZENU_OT_add_vertex_layer(bpy.types.Operator):
    bl_label = 'Add Vertex Layer'
    bl_idname = 'zenu.add_vertex_layer'
    bl_options = {'UNDO'}
    name: bpy.props.StringProperty(default='Folder')
    uid: bpy.props.StringProperty()
    parent_uid: bpy.props.StringProperty()
    is_folder: bpy.props.BoolProperty(default=False)

    def get_max_index(self, context: bpy.types.Context, data: VertexLayer):
        max_index = 1

        if self.is_folder:
            for i in context.active_object.zenu_vertex_layer:
                if i.index > max_index:
                    max_index = i.index
            max_index += 1000
        else:
            for i in context.active_object.zenu_vertex_layer:
                if i.parent_uid != data.uid:
                    continue

                if i.index > max_index:
                    max_index = i.index
            max_index += 1

        return max_index

    def add_vertex_color(self, context: bpy.types.Context, data: VertexLayer):
        if data is None:
            return

        if data.is_folder:
            return

        obj = context.active_object
        # v = obj.data.vertex_colors.new(name=data.uid, do_init=False)
        # bpy.ops.paint.vertex_color_set()
        # context.active_

        bpy.ops.geometry.color_attribute_add(name=data.uid, color=(0, 0, 0, 1), domain='CORNER', data_type='BYTE_COLOR')
        # print(obj.data.vertex_colors.active.name)
        # obj.data.vertex_colors.active.name = data.uid

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        data = get_active_layer(context.active_object)

        max_index = self.get_max_index(context, data)
        uid = uuid4().hex
        item = context.active_object.zenu_vertex_layer.add()
        item.name = self.name
        item.uid = uid
        item.is_folder = self.is_folder
        item.index = max_index

        if not self.is_folder:
            # item.uid = uid
            self.add_vertex_color(context, item)

        if self.is_folder:
            item.name = 'Folder'
        else:
            item.name = 'Layer'

        if data and not self.is_folder:
            if data.is_folder:
                item.parent_uid = data.uid
            else:
                item.parent_uid = data.parent_uid

        sort_vertex_layers(context.active_object)
        obj.zenu_vertex_layer_active += 1

        update_window(all_w=True)
        return {'FINISHED'}


class ZENU_OT_remove_vertex_layer(bpy.types.Operator):
    bl_label = 'Remove Vertex Layer'
    bl_idname = 'zenu.remove_vertex_layer'
    bl_options = {'UNDO'}

    def remove_vertex_color(self, context: bpy.types.Context, data: VertexLayer):
        obj = context.active_object

        for color in obj.data.vertex_colors:
            if color.name == data.uid:
                obj.data.vertex_colors.remove(color)
                break

    def execute(self, context: bpy.types.Context):
        data = get_active_layer(context.active_object)
        obj = bpy.context.active_object

        if data.is_folder:
            layers = get_folder_layers(obj, data)
            for layer in layers:
                self.remove_vertex_color(context, layer)

            layers.append(data)
            remove_bulk_layer(obj, layers)

            return {'FINISHED'}

        self.remove_vertex_color(context, data)
        remove_layer(obj, data)
        # obj.zenu_vertex_layer.remove(obj.zenu_vertex_layer_active)
        obj.zenu_vertex_layer_active -= 1

        sort_vertex_layers(obj)
        return {'FINISHED'}


class ZENU_OT_create_node_group(bpy.types.Operator):
    bl_label = 'Create Node Group'
    bl_idname = 'zenu.create_node_group'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        generate_shader(obj)
        return {'FINISHED'}


class ZENU_UL_vertex_paint_list(bpy.types.UIList):
    def draw_item(self, context, layout: bpy.types.UILayout, data, item: VertexLayer, icon, active_data,
                  active_propname):

        obj = context.active_object

        if item.is_folder:
            layout.prop(item, 'name', text='', emboss=False)
        else:
            folders = {
                item.uid: item for index, item in enumerate(obj.zenu_vertex_layer) if item.is_folder
            }

            row = layout.row()
            row.separator(factor=1)
            row.prop(item, 'name', emboss=False, text='')

            try:
                data = folders[item.parent_uid]
                row.label(text=data.name)
            except Exception:
                pass


class ZENU_PT_vertex_paint(BasePanel):
    bl_label = 'Vertex Paint'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        obj = context.active_object

        data = get_active_layer(obj)
        vertex_layers = get_shader(obj)

        layout.operator(ZENU_OT_clear_vertex_layer.bl_idname)
        layout.operator(ZENU_OT_sort_vertex_layer.bl_idname)
        layout.operator(ZENU_OT_move_vertex_layer.bl_idname)
        layout.operator(ZENU_OT_random_vertex_layer.bl_idname)
        layout.operator(ZENU_OT_create_node_group.bl_idname)

        row = layout.row(align=True)
        row.template_list('ZENU_UL_vertex_paint_list', '',
                          context.object, 'zenu_vertex_layer',
                          context.object, 'zenu_vertex_layer_active')

        col = row.column(align=True)

        if data:
            op = col.operator(ZENU_OT_add_vertex_layer.bl_idname, icon='ADD', text='')
            op.is_folder = False
            col.operator(ZENU_OT_remove_vertex_layer.bl_idname, icon='REMOVE', text='')

        op = col.operator(ZENU_OT_add_vertex_layer.bl_idname, icon='NEWFOLDER', text='')
        op.is_folder = True

        if data:
            node = None

            for node in vertex_layers.nodes:
                if node.name == data.uid:
                    node = node
                    break

            if isinstance(node, bpy.types.ShaderNodeRGB):
                layout.prop(node.outputs[0], 'default_value', text='')

            if isinstance(node, bpy.types.ShaderNodeMix):
                layout.prop(node, 'blend_type', text='')
                layout.prop(node.inputs[7], 'default_value', text='')


reg, unreg = bpy.utils.register_classes_factory((
    VertexLayer,
    ZENU_OT_move_vertex_layer,
    ZENU_OT_add_vertex_layer,
    ZENU_OT_remove_vertex_layer,
    ZENU_OT_sort_vertex_layer,
    ZENU_OT_clear_vertex_layer,
    ZENU_OT_random_vertex_layer,
    ZENU_OT_create_node_group,
    ZENU_UL_vertex_paint_list,
    ZENU_PT_vertex_paint
))


def on_select_layer(self: bpy.types.Object, context):
    layer = get_active_layer(self)
    if layer is None:
        return

    if layer.is_folder:
        return

    for color in self.data.vertex_colors:
        if layer.uid == color.name:
            self.data.vertex_colors.active = color
            break


def register():
    reg()
    bpy.types.Object.zenu_vertex_layer = bpy.props.CollectionProperty(type=VertexLayer)
    bpy.types.Object.zenu_vertex_layer_active = bpy.props.IntProperty(update=on_select_layer)


def unregister():
    unreg()

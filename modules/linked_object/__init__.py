import bpy
from ...base_panel import BasePanel
from ...utils import get_path_to_asset

LINK_PREFIX = '[ZLK]'
MATERIAL_REPLACE_NAME = f'{LINK_PREFIX} Material Replace'
COPY_OBJECT_NAME = f'{LINK_PREFIX} Copy Object'
MOD_REPLACE_MATERIAL = 'ZENU Replace Material'
MOD_COPY_OBJECT = 'ZENU Copy Object'


def get_node(name: str) -> bpy.types.NodeTree | None:
    path = get_path_to_asset('linked_copy/ZenuLinkedGeoNodes.blend')
    node = bpy.data.node_groups.get(name)

    if node is not None:
        return node

    with bpy.data.libraries.load(path) as (data_from, data_to):
        data_to.node_groups = [name]

    return data_to.node_groups[0]


def get_copy_node() -> bpy.types.NodeTree:
    return get_node(MOD_COPY_OBJECT)


def get_material_replace_node() -> bpy.types.NodeTree:
    return get_node(MOD_REPLACE_MATERIAL)


def add_replace_material(obj: bpy.types.Object, old: bpy.types.Material, new: bpy.types.Material, name: str = None):
    geo_node = get_material_replace_node()

    if name is None:
        name = MATERIAL_REPLACE_NAME
    else:
        name = f'{LINK_PREFIX} {name}'

    mod = obj.modifiers.new(name, type='NODES')
    mod.node_group = geo_node

    old_mat_socket_name = geo_node.interface.items_tree['Old'].identifier
    new_mat_socket_name = geo_node.interface.items_tree['New'].identifier

    mod[old_mat_socket_name] = old
    mod[new_mat_socket_name] = new
    mod.show_expanded = False
    return mod


def add_copy_object(src: bpy.types.Object, dst: bpy.types.Object, name: str = None):
    geo_node = get_copy_node()
    object_socket = geo_node.interface.items_tree['Object'].identifier
    delete_socket = geo_node.interface.items_tree['Delete Group'].identifier

    if name is None:
        name = COPY_OBJECT_NAME
    else:
        name = f'{LINK_PREFIX} {name}'

    mod = dst.modifiers.new(name, type='NODES')
    mod.node_group = geo_node
    mod[object_socket] = src
    mod.show_expanded = False

    with bpy.context.temp_override(object=dst):
        bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name=delete_socket, modifier_name=mod.name)


def get_copy_object(obj: bpy.types.Object):
    geo_node = bpy.data.node_groups[MOD_COPY_OBJECT]
    object_socket = geo_node.interface.items_tree['Object'].identifier

    for mod in obj.modifiers:
        if mod.type != 'NODES': continue
        if mod.node_group != geo_node: continue

        return mod[object_socket]


class ZENU_OT_add_linked_object(bpy.types.Operator):
    bl_label = 'Add Linked Object'
    bl_idname = 'zenu.add_linked_object'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        for ob in context.selected_objects:
            name = ob.name + '_LinkedCopy'
            mesh = bpy.data.meshes.new(name)
            obj_new = bpy.data.objects.new(name, mesh)
            obj_new.location = bpy.context.scene.cursor.location
            add_copy_object(ob, obj_new)

            context.collection.objects.link(obj_new)
        return {'FINISHED'}


class ZENU_OT_add_linked_collection(bpy.types.Operator):
    bl_label = 'Add Linked Collection'
    bl_idname = 'zenu.add_linked_collection'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        collection = context.collection

        # for i in collection.objects

        print(collection)
        return {'FINISHED'}


class ZENU_OT_add_replace_material(bpy.types.Operator):
    bl_label = 'Add Replace Material'
    bl_idname = 'zenu.add_replace_material'
    bl_options = {'UNDO'}
    new_material: bpy.props.StringProperty(name='New')

    def invoke(self, context, event):
        context.scene.zenu_material_selector_slot = None
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        col = layout.column(align=True)
        col.prop(context.scene, 'zenu_material_selector_slot', text='Old')
        col.prop_search(self, 'new_material', bpy.data, 'materials', text='New')

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        old_mat = context.scene.zenu_material_selector_slot
        new_mat = bpy.data.materials[self.new_material]

        add_replace_material(obj, old_mat, new_mat)

        return {'FINISHED'}


class ZENU_OT_duplicate_all_materials(bpy.types.Operator):
    bl_label = 'Duplicate All Materials'
    bl_idname = 'zenu.duplicate_all_materials'
    bl_options = {'UNDO'}

    type_rename: bpy.props.EnumProperty(items=(
        ('POSTFIX', 'Postfix', ''),
        ('PREFIX', 'Prefix', ''),
        ('REPLACE', 'Replace', ''),
    ), name='Replace Name')

    value: bpy.props.StringProperty()

    def rename_material(self, name: str, value: str, type: str):
        if type == 'POSTFIX':
            return name + value

        if type == 'PREFIX':
            return value + name

        if type == 'Replace':
            return value

        return name

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        layout.prop(self, 'type_rename', text='')
        col = layout.column(align=True)
        col.prop(self, 'value', text='Text')

    def execute(self, context: bpy.types.Context):
        value = self.value
        type_rename = self.type_rename

        for obj in context.selected_objects:
            obj.data.materials.clear()
            obj_mat = get_copy_object(obj)
            for slot in obj_mat.material_slots:
                old_mat = slot.material

                new_mat = old_mat.copy()
                new_mat.name = self.rename_material(old_mat.name, value, type_rename)

                add_replace_material(obj, old_mat, new_mat, name=f'{old_mat.name} -> {new_mat.name}')
                obj.data.materials.append(new_mat)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ZENU_OT_remove_replace_material(bpy.types.Operator):
    bl_label = 'Remove Replace Material'
    bl_idname = 'zenu.remove_replace_material'
    mod_name: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        mod = context.active_object.modifiers[self.mod_name]
        context.active_object.modifiers.remove(mod)
        return {'FINISHED'}


class ZENU_PT_linked_objects(BasePanel):
    bl_label = 'Linked Objects'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True
        obj = context.active_object

        if obj is None:
            return

        layout.operator(ZENU_OT_add_linked_object.bl_idname)
        layout.operator(ZENU_OT_add_replace_material.bl_idname)
        layout.operator(ZENU_OT_duplicate_all_materials.bl_idname)
        # layout.operator(ZENU_OT_add_linked_collection.bl_idname)

        geo_mat_rep = get_material_replace_node()
        geo_copy = get_copy_node()

        if geo_mat_rep is None or geo_copy is None:
            return

        old_material_socket_name = geo_mat_rep.interface.items_tree['Old'].identifier
        new_material_socket_name = geo_mat_rep.interface.items_tree['New'].identifier

        delete_group_id = geo_copy.interface.items_tree['Delete Group'].identifier
        object_id = geo_copy.interface.items_tree['Object'].identifier

        copy_box = layout.box()

        for mod in obj.modifiers:
            if mod.type != 'NODES': continue

            if mod.node_group == geo_copy:
                mod_obj: bpy.types.Object = mod[object_id]
                copy_box.prop_search(mod, f'["{delete_group_id}_attribute_name"]', mod_obj, 'vertex_groups',
                                     text='Delete')

            if mod.node_group != geo_mat_rep: continue
            box = layout.box().column(align=True)

            col = box.row()
            col.label(text=mod.name)
            op = col.operator(ZENU_OT_remove_replace_material.bl_idname, emboss=False, text='', icon='X')
            op.mod_name = mod.name

            box.prop_search(mod, f'["{old_material_socket_name}"]', bpy.data, 'materials', text='Old Mat')
            box.prop_search(mod, f'["{new_material_socket_name}"]', bpy.data, 'materials', text='New Mat')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_linked_objects,
    ZENU_OT_add_linked_object,
    ZENU_OT_add_replace_material,
    ZENU_OT_remove_replace_material,
    ZENU_OT_duplicate_all_materials,
    ZENU_OT_add_linked_collection
))


def material_slots_filter(self, material: bpy.types.Material):
    obj = bpy.context.active_object
    geo_node = bpy.data.node_groups[MOD_COPY_OBJECT]
    object_socket = geo_node.interface.items_tree['Object'].identifier

    for mod in obj.modifiers:
        if mod.type != 'NODES': continue
        if mod.node_group != geo_node: continue

        obj = mod[object_socket]
        break

    for i in obj.material_slots:
        if i.material == material:
            return True

    return False


def register():
    bpy.types.Scene.zenu_material_selector_slot = bpy.props.PointerProperty(
        type=bpy.types.Material,
        poll=material_slots_filter
    )
    reg()


def unregister():
    unreg()

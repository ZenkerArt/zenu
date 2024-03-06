import bpy
from idprop.types import IDPropertyGroup
from rna_prop_ui import rna_idprop_quote_path
from ...base_panel import BasePanel
from ...utils import check_mods, is_type, COLOR_ICONS


class ShowLevel:
    NORMAL = 'NORMAL'
    DEBUG = 'DEBUG'


enum_icons = [
    (i, ' '.join(i.split('_')).title(), '', i, index) for index, i in enumerate(COLOR_ICONS)
]

enum_show_levels = (
    (ShowLevel.NORMAL, 'Normal', ''),
    (ShowLevel.DEBUG, 'Debug', ''),
)


def update(self, context):
    arm: bpy.types.Armature = context.active_object.data
    for i in arm.collections:
        if self == i.zenu_layer:
            i.is_visible = self.is_visible


class ZENU_UL_bone_collection(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item
        name = slot.zenu_layer.name
        if name:
            layout.prop(slot.zenu_layer, 'name', text='', icon=slot.zenu_layer.icon, emboss=False)
        else:
            layout.prop(slot, 'name', text='', icon=slot.zenu_layer.icon, emboss=False)
        layout.prop(slot.zenu_layer, 'is_show',
                    text='', icon='HIDE_OFF' if slot.zenu_layer.is_show else 'HIDE_ON',
                    emboss=False)


class BoneLayerData(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='UI Layer Name')
    index: bpy.props.IntProperty(name='Layer Order', default=0)
    show_level: bpy.props.EnumProperty(name='Show Level', items=enum_show_levels)
    is_show: bpy.props.BoolProperty(name='Show Layer In UI', default=False)
    is_visible: bpy.props.BoolProperty(name='Is Visible', default=False, update=update)

    icon: bpy.props.EnumProperty(
        items=enum_icons,
        default='SEQUENCE_COLOR_01'
    )


class ZENU_OT_toggle_layer_view(bpy.types.Operator):
    bl_label = 'Activate Bone Layer'
    bl_idname = 'zenu.activate_layer'
    bl_options = {'UNDO'}
    name: bpy.props.StringProperty(name='Layer Name')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Armature)

    def execute(self, context: bpy.types.Context):
        arm: bpy.types.Armature = context.active_object.data
        arm.collections[self.name].is_visible = not arm.collections[self.name].is_visible
        return {'FINISHED'}


class ZENU_PT_bone_layer_setting(BasePanel):
    bl_label = 'Bone Layer'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Armature)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        arm: bpy.types.Armature = obj.data
        zenu_layer = arm.collections.active.zenu_layer

        row = layout.row(align=True)

        row.template_list("ZENU_UL_bone_collection", "", obj.data, "collections", obj.data.collections,
                          "active_index")

        col = row.column(align=True)
        col.operator("armature.collection_add", icon='ADD', text="")
        col.operator("armature.collection_remove", icon='REMOVE', text="")
        col.separator()
        col.operator("armature.collection_move", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("armature.collection_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        lay = layout.column(align=True)
        lay.prop(zenu_layer, 'name', text='')
        lay.prop(zenu_layer, 'index')
        lay.prop(zenu_layer, 'show_level', expand=True)
        row = lay.row(align=True)
        row.scale_x = 100
        row.scale_y = 2
        row.prop(zenu_layer, 'icon', text='', expand=True)


class BoneLayer:
    _layout: bpy.types.UILayout

    def __init__(self, layout: bpy.types.UILayout, text: str = ''):
        box = layout

        # if text:
        #     box = box.box()
        #     box.label(text=text)
        #     box = box.row(align=True)
        # else:
        #     box = box.row(align=True)

        box.scale_y = 1.4
        self._layout = box.row(align=True)

    @property
    def layout(self):
        return self._layout


class BoneLayers:
    _layers: dict[str | int, BoneLayer]
    _layout: bpy.types.UILayout

    def __init__(self, layout: bpy.types.UILayout):
        self._layers = {}
        self._layout = layout

    def get_layer(self, index: int, name: str = None):
        layer = self._layers.get(index)
        if layer is None:
            layer = BoneLayer(self._layout, name)
            self._layers[index] = layer

        return layer

    def draw(self):
        lst = []

        for index, layer in self._layers.items():
            lst.append((index, layer))


class ZENU_PT_bone_layer(BasePanel):
    bl_label = 'Bone Layer'
    bl_context = ''

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Armature)

    def draw_layers(self, layout: bpy.types.UILayout, arm: bpy.types.Armature):
        layout = layout.box().column(align=True)
        layers = BoneLayers(layout)

        for collection in arm.collections:
            layer_info: BoneLayerData = collection.zenu_layer
            if layer_info.show_level != arm.zenu_show_level:
                continue

            if not layer_info.is_show:
                continue

            name = layer_info.name or collection.name
            lay = layers.get_layer(layer_info.index)
            lay.layout.prop(layer_info, 'is_visible', text=name, icon=layer_info.icon)

    def draw_bone_property(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        if not check_mods('p'):
            return

        pose_bone = context.active_pose_bone
        props = [i for i in pose_bone.items() if not isinstance(i[1], IDPropertyGroup)]

        if not props:
            return

        box = layout.box().column(align=True)
        box.scale_y = 1.4
        box.label(text='Properties')

        for i in props:
            box.prop(pose_bone, rna_idprop_quote_path(i[0]))

    def draw(self, context: bpy.types.Context):
        arm: bpy.types.Armature = context.active_object.data
        layout = self.layout

        col = layout.row()
        col.scale_y = 1.5
        col.prop(arm, 'zenu_show_level', expand=True)

        self.draw_layers(layout, arm)
        self.draw_bone_property(context, layout)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_bone_layer_setting,
    ZENU_PT_bone_layer,
    BoneLayerData,
    ZENU_UL_bone_collection,
    ZENU_OT_toggle_layer_view
))


def register():
    reg()
    bpy.types.Armature.zenu_show_level = bpy.props.EnumProperty(items=enum_show_levels, name='Show Level')
    bpy.types.BoneCollection.zenu_layer = bpy.props.PointerProperty(type=BoneLayerData)


def unregister():
    unreg()

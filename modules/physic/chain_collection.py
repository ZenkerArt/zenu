import bpy


class ZENU_UL_chain_collection(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        col = layout.column()
        col.label(text=item.obj.name)


class ZChainCollection(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    constraints: bpy.props.StringProperty()


def draw(context: bpy.types.Context, layout: bpy.types.UILayout):
    scene = context.scene

    layout.template_list('ZENU_UL_constraints_list', '',
                         scene, 'zenu_physic_chain_collection',
                         scene, 'zenu_physic_chain_collection_active')

reg, unreg = bpy.utils.register_classes_factory((
    ZChainCollection,
    ZENU_UL_chain_collection,
))


def register():
    reg()
    bpy.types.Scene.zenu_physic_chain_collection = bpy.props.CollectionProperty(type=ZChainCollection)
    bpy.types.Scene.zenu_physic_chain_collection_active = bpy.props.IntProperty()


def unregister():
    unreg()

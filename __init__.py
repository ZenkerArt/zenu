from . import physic_manager, modifier_search, utils_panel, lod_manger, align_tools, timemarkers
import bpy

bl_info = {
    "name": "zenu",
    "author": "Zenker",
    "description": "",
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}


class ZenUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    physic_groups: bpy.props.CollectionProperty(type=physic_manager.property_groups.PhysicGroup)

    def draw(self, context):
        layout = self.layout
        # print(__name__)


modules = (
    # bone,
    utils_panel,
    physic_manager,
    align_tools,
    modifier_search,
    timemarkers,
    lod_manger,
    # constraint_manager,
)


def register():
    for i in modules:
        i.register()
    bpy.utils.register_class(ZenUtilsPreferences)


def unregister():
    for i in modules:
        i.unregister()
    bpy.utils.unregister_class(ZenUtilsPreferences)

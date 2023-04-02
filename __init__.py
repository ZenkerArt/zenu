from . import physic_manager, shape_key_viewer, bone, utils_panel, lod_manger

bl_info = {
    "name": "zenu",
    "author": "Zenker",
    "description": "",
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}

modules = (
    # bone,
    utils_panel,
    physic_manager,
    shape_key_viewer,
    lod_manger
)


def register():
    for i in modules:
        i.register()


def unregister():
    for i in modules:
        i.unregister()

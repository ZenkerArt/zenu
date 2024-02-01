import bpy
from .data_transfer import ZENU_OT_data_transfer
from .edger import ZENU_OT_edger
from .extract_mesh import ZENU_OT_extract_mesh
from ..menu_manager import OperatorItem, menu_manager

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_edger,
    ZENU_OT_extract_mesh,
    ZENU_OT_data_transfer
))


def register():
    menu_manager.right.add_list([
        OperatorItem(ZENU_OT_edger.bl_idname),
        OperatorItem(ZENU_OT_extract_mesh.bl_idname),
        OperatorItem(ZENU_OT_data_transfer.bl_idname)
    ])
    reg()


def unregister():
    unreg()

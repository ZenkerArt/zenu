from dataclasses import dataclass

import bpy
from .data_transfer import ZENU_OT_data_transfer
from .edger import ZENU_OT_edger
from .extract_mesh import ZENU_OT_extract_mesh
from .material import ZENU_OT_assign_material_active_polygon
from .smart_array import ZENU_OT_array
from .smart_bevel import ZENU_OT_bevel
from ..menu_manager import OperatorItem, menu_manager
from ..menu_manager.menu_group import OperatorItemList

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_edger,
    ZENU_OT_extract_mesh,
    ZENU_OT_data_transfer,
    ZENU_OT_assign_material_active_polygon,
    ZENU_OT_array,
    ZENU_OT_bevel
))


@dataclass
class Color:
    icon: str = None
    name: str = ''
    color: tuple = (0, 0, 0)


def register():
    # menu_manager.clear()
    colors = [
        Color(icon='SEQUENCE_COLOR_01',
              name='ZENU_RED',
              color=(1, 0, 0)),
        Color(icon='SEQUENCE_COLOR_04',
              name='ZENU_GREEN',
              color=(0, 1, 0)),
        Color(icon='SEQUENCE_COLOR_05',
              name='ZENU_BLUE',
              color=(0.132258, 0.564927, 1.0)),
        Color(icon='SEQUENCE_COLOR_03',
              name='ZENU_ORANGE',
              color=(1.0, 0.812537, 0.10294)),
    ]

    menu_manager.right.add_list([
        OperatorItem(ZENU_OT_edger.bl_idname),
        OperatorItem(ZENU_OT_extract_mesh.bl_idname),
        OperatorItem(ZENU_OT_data_transfer.bl_idname),
        OperatorItemList('Color Selector', [
            OperatorItem(ZENU_OT_assign_material_active_polygon.bl_idname,
                         vars={'color': i.color, 'name': i.name},
                         op_id=i.name,
                         text='',
                         icon=i.icon
                         ) for i in colors
        ]),
    ])

    menu_manager.left.add_list([
        OperatorItem(ZENU_OT_array.bl_idname, icon='MOD_ARRAY'),
        OperatorItemList('bavel', [
            OperatorItem(ZENU_OT_bevel.bl_idname,
                         icon='MOD_BEVEL',
                         vars={'edit': False}),
            OperatorItem(ZENU_OT_bevel.bl_idname,
                         icon='OUTLINER_DATA_MESH',
                         op_id='bavel_edit',
                         text='',
                         vars={'edit': True}),
        ])
    ])

    reg()


def unregister():
    # menu_manager.clear()
    unreg()

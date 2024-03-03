import random

import bpy
from ..menu_manager import menu_timeline
from . import animation_offset, smart_noise
from ..menu_manager.menu_group import OperatorItemList, OperatorItem

reg, unreg = bpy.utils.register_classes_factory((
    *animation_offset.classes,
    *smart_noise.classes
))


def register():
    reg()
    menu_timeline.right.add(OperatorItem(smart_noise.ZENU_OT_anim_noise.bl_idname))
    menu_timeline.right.add(OperatorItemList('SmartNoise', [
        OperatorItem(smart_noise.ZENU_OT_anim_noise_blend.bl_idname, text='', icon='SPHERECURVE'),
        OperatorItem(smart_noise.ZENU_OT_anim_noise_edit.bl_idname, text='', icon='EDITMODE_HLT'),
        OperatorItem(smart_noise.ZENU_OT_anim_noise_move.bl_idname, text='', icon='ARROW_LEFTRIGHT'),
        OperatorItem(smart_noise.ZENU_OT_anim_noise_remove.bl_idname, text='', icon='TRASH'),
        OperatorItem(smart_noise.ZENU_OT_anim_noise_property_edit.bl_idname, text='', icon='PROPERTIES'),
    ]))
    bpy.types.Scene.zenu_animation_offset = bpy.props.PointerProperty(type=animation_offset.AnimationOffsetProps)


def unregister():
    unreg()

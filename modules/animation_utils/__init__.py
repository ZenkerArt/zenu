import random

import bpy
from ..menu_manager import menu_timeline
from . import animation_offset, smart_noise
from ..menu_manager.menu_group import OperatorItemList, OperatorItem
from . import test
from . import timeline, nla, keying_set
from ...utils import register_modules, unregister_modules

reg, unreg = bpy.utils.register_classes_factory((
    *animation_offset.classes,
    *smart_noise.classes,
    *test.classes
))

modules = (
    timeline,
    nla,
    keying_set
)


def register():
    reg()
    register_modules(modules)
    menu_timeline.right.add(test.ZENU_OT_anim_enable.bl_idname)
    menu_timeline.right.add(smart_noise.ZENU_OT_anim_noise.bl_idname)
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
    test.draw.deactivate()
    unregister_modules(modules)

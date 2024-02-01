import bpy
from ...base_panel import BasePanel


class IKSwitcherProperties(bpy.types.PropertyGroup):
    base: bpy.props.PointerProperty()



class ZENU_PT_ik_switcher(BasePanel):
    bl_label = 'IK Switcher'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.label(text='Text1')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_ik_switcher,
))


def register():
    reg()


def unregister():
    unreg()

import bpy

class ZENU_PT_render_quene(BasePanel):
    bl_label = 'render_quene'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        pass

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_render_quene,
))


def register():
    reg()


def unregister():
    unreg()

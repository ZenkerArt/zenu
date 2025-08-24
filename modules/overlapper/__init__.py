import bpy

class ZENU_PT_overlaper(BasePanel):
    bl_label = 'Overlaper'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        pass

reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_overlaper,
))


def register():
    reg()


def unregister():
    unreg()

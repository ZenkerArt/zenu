import bpy
from ...base_panel import BasePanel
from .constraint_issues import constraint_analyze


class ZENU_PT_analyze(BasePanel):
    bl_label = 'Analyze'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_analyze,
))


def register():
    reg()
    constraint_analyze.register()


def unregister():
    unreg()
    constraint_analyze.unregister()

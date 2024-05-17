import bpy
from ...base_panel import BasePanel
from .constraint_issues import constraint_analyze


class ZENU_PT_search(BasePanel):
    bl_label = 'Search'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_search,
))


def register():
    reg()
    constraint_analyze.register()


def unregister():
    unreg()
    constraint_analyze.unregister()

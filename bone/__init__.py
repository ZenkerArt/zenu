import bpy
from bpy.types import Context
from .bone_list import ZENU_UL_bone_select
from ..base_panel import BasePanel


class ZENU_PT_bone(BasePanel):
    bl_label = "My Tool"

    def draw(self, context: Context):
        layout = self.layout
        obj = context.active_object
        # layout.template_list("ZENU_UL_bone_select", "", obj, "material_slots", obj, "active_material_index")


register, unregister = bpy.utils.register_classes_factory((
    ZENU_UL_bone_select,
    ZENU_PT_bone,
))

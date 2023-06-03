import bpy
from .base_clasess import ObjectDrawer
from ....utils import get_modifier


class ObjectModifyers(ObjectDrawer):

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        mods = {
            'Subdiv': bpy.types.SubsurfModifier,
            'Cloth': bpy.types.ClothModifier,
            'Solidify': bpy.types.SolidifyModifier
        }
        layout = layout.column(align=True)

        for key, value in mods.items():
            mod = get_modifier(context.active_object, value)
            if mod:
                layout.prop(mod, 'show_viewport', text=key)


classes = (
    ObjectModifyers,
)

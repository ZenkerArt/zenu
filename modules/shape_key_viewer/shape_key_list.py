import bpy


class ZENU_UL_shape_key_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')
        layout.prop(item, 'value', emboss=False, text='')

from . import ZenuUIList
from ...base_panel import BasePanel
import bpy

class ExampleListItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    camera_markers: bpy.props.StringProperty()
    isolate_camera: bpy.props.StringProperty()

    use_in: bpy.props.EnumProperty(items={
        ('VR', 'Use In VR', ''),
        ('2D', 'Use In 2D', ''),
    })


class ExampleList(ZenuUIList[ExampleListItem]):
    name = 'example_list'
    _property_group = ExampleListItem

    def _draw(self, layout, item):
        layout.prop(item, 'name', text='', emboss=False)

    def add(self):
        item = super().add()
        item.name = 'No Name'
        item.camera_markers = '{}'
        return item

    def _on_select(self):
        pass


example_list = ExampleList()

class ZENU_PT_example(BasePanel):
    bl_label = "example list"
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        example_list.draw_ui(layout=layout)



def register():
    example_list.register()


def unregister():
    example_list.unregister()

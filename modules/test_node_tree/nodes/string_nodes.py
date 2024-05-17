import bpy
from ..base_node import BaseNode


class ZENU_ND_string(BaseNode):
    bl_label = 'Get Bone'

    def init(self, context):
        # self.input_string('Text')
        self.output_string('Text')

    def draw_buttons(self, context, layout: bpy.types.UILayout):
        pass

    def execute(self, context):
        pass
        # print(123)


nodes = (
    ZENU_ND_string,
)

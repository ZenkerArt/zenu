import bpy
from .rig_module import RigModule


class TestRig(RigModule):
    rig_name = 'Test Rig'

    test_val: bpy.props.IntProperty(name='Test')
    test2_val: bpy.props.IntProperty(name='Test 2')
    test3_val: bpy.props.IntProperty(name='Test 3')

    def draw(self, props: bpy.types.bpy_struct, context: bpy.types.Context):
        self.layout.prop(props, self.get_prop_name('test_val'))

    def execute_pose(self, context: bpy.types.Context):
        print(self.test3_val)
        print(self.bone)

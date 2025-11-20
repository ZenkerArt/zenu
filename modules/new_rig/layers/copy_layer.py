import bpy
from ..rig_lib import RigContext, RigLayer


class CopyLayer(RigLayer):
    def replace_data(self, obj: bpy.types.Object, data: bpy.types.Armature):
        old_data = obj.data
        name = old_data.name

        old_data.name = 'temp000001'
        
        obj.data = data
        
        bpy.data.armatures.remove(old_data)
        data.name = name
        
    
    def clear_bones(self, obj: bpy.types.Object):
        self.replace_data(obj, bpy.data.armatures.new(obj.data.name))
    
    def copy_to(self, obj1: bpy.types.Object, obj2: bpy.types.Object):
        self.replace_data(obj1, obj2.data.copy())

    def execute(self, context: RigContext):
        self.copy_to(context.new_armature, context.original_armature)
        
        bpy.ops.object.mode_set(mode='POSE')
        for i in context.new_armature.pose.bones:
            for con in i.constraints:
                i.constraints.remove(con)

        # old_arm = context.org_arm
        # new_arm = context.new_arm

        # print(old_arm, new_arm)
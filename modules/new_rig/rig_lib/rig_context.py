import bpy
from .deps_inject import DepsInject


class RigContext:
    original_armature: bpy.types.Object
    new_armature: bpy.types.Object
    deps: DepsInject

    @property
    def org_arm(self) -> bpy.types.Armature:
        return self.original_armature.data
    
    @property
    def new_arm(self) -> bpy.types.Armature:
        return self.new_armature.data

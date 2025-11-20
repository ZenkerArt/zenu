import bpy


class RigBone:
    _arm: bpy.types.Object
    _bone: str

    def __init__(self, arm: bpy.types.Object, bone: str):
        self._arm = arm
        if hasattr(bone, 'name'):
            self._bone = bone.name
        else:
            self._bone = bone

    @property
    def mark_copy_constraints_from(self) -> str:
        return self.props.copy_constraint_from

    @mark_copy_constraints_from.setter
    def mark_copy_constraints_from(self, bone_name: str):
        self.props.copy_constraint_from = bone_name

    @property
    def name(self):
        return self._bone

    @property
    def arm(self):
        return self._arm

    @property
    def pose(self):
        return self._arm.pose.bones[self._bone]

    @property
    def edit(self) -> bpy.types.EditBone:
        return self._arm.data.edit_bones[self._bone]

    @property
    def base(self) -> bpy.types.Bone:
        return self._arm.data.bones[self._bone]

    @property
    def props(self):
        return self.base.zenu_rig_component_props

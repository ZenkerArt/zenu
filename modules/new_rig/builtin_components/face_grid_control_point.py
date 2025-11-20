from typing import Any
import bpy
from mathutils import Vector
from ..layers import BoneCollectorLayer, CopyConstraintLayer, RigComponentsLayer, StyleLayer, BoneCollectionLayer
from ..rig_lib import RigBone, RigComponent, RigContext
from .face_grid import FaceGrid

class FaceGridPointControl(RigComponent):
    name = 'Face Grid Control'

    def __init__(self):
        super().__init__()

        self.points = []
        self.tail = []
        self.bone_groups = []

    @classmethod
    def draw(cls, context: bpy.types.Context, data: Any, layout: bpy.types.UILayout):
        layout.prop(data, cls.get_prop_name('subtype'))

    def execute_edit(self, context: RigContext, bones_collector: BoneCollectorLayer, layers: RigComponentsLayer, const: CopyConstraintLayer, style: StyleLayer, coll_ls: BoneCollectionLayer):
        fg = layers.get_comp(FaceGrid)
        
        for i in bones_collector.get_rig_bones_by_type(self):
            i.edit.use_deform = False
            p = fg.points.get_point(i.edit.head)
            p.bone.edit.parent = i.edit
            
            style.apply_shape(i, i.props.shape)
            
            const.copy_from(
                RigBone(context.original_armature, i.name),
                i)
            
            coll = i.edit.collections[0]
            
            st_coll = coll_ls.get_collection(f'{coll.name} Tweak')
            st_coll.assign(i.edit)
            
            st_coll.parent = coll

    def execute_pose(self, context: RigContext, bones_collector: BoneCollectorLayer):
        pass
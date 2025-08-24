import bpy
from bpy.app.handlers import persistent
from bpy.types import Context
from . import physic, chain_collection
from .settings import ZPhysicSettings, get_physic_settings, ZPhysicSettingsBone
from ...base_panel import BasePanel


@persistent
def load_handler(dummy):
    physic.loop()
    # if root_node:
    #     root_node.solve()


class ZENU_OT_add_bone(bpy.types.Operator):
    bl_label = 'Add Bone'
    bl_idname = 'zenu.add_bone'

    def add_empty(self, context: bpy.types.Context, name: str):
        empty = bpy.data.objects.new(name, None)
        context.view_layer.layer_collection.collection.objects.link(empty)
        return empty

    def execute(self, context: bpy.types.Context):
        physic.init()
        return {'FINISHED'}


class ZENU_OT_zclear(bpy.types.Operator):
    bl_label = 'Clear Bone'
    bl_idname = 'zenu.zclear'

    def execute(self, context: bpy.types.Context):
        physic.clear()
        return {'FINISHED'}


class ZENU_PT_phyisc(BasePanel):
    bl_label = 'Physic'
    bl_context = ''

    def draw(self, context: Context):
        layout = self.layout
        chain_collection.draw(context, layout)

        # layout.prop(get_physic_settings(), 'auto_sort', icon='RADIOBUT_ON' if auto_sort else 'RADIOBUT_OFF')
        # if context.selected_pose_bones is None:
        #     return
        #
        # if not auto_sort:
        #     col = layout.column(align=True)
        #     for bone in context.selected_pose_bones:
        #         row = col.row()
        #         row.prop(bone.zenu_physic_settings, 'order', text='')
        #         row.label(text=bone.name)

        layout.operator(ZENU_OT_add_bone.bl_idname)
        layout.operator(ZENU_OT_zclear.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_phyisc,
    ZENU_OT_add_bone,
    ZENU_OT_zclear,
    ZPhysicSettings,
    ZPhysicSettingsBone
))


def register():
    bpy.types.Scene.zenu_float_curve = bpy.props.FloatProperty()
    bpy.app.handlers.frame_change_post.append(load_handler)
    reg()
    physic.reg()
    chain_collection.register()
    bpy.types.Scene.zenu_physic_settings = bpy.props.PointerProperty(
        type=ZPhysicSettings)
    bpy.types.PoseBone.zenu_physic_settings = bpy.props.PointerProperty(
        type=ZPhysicSettingsBone)


def unregister():
    bpy.app.handlers.frame_change_post.remove(load_handler)
    unreg()
    physic.unreg()
    chain_collection.unregister()

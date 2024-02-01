import bpy
from bpy.types import Context
from .physic_objects import PhysicHandler, FollowObject
from ...base_panel import BasePanel
from ...utils import check_mods

physic_objects = PhysicHandler()


def remove_lr_shapes(obj, name: str):
    left_shape = obj.data.shape_keys.key_blocks.get(name + '.L')
    right_shape = obj.data.shape_keys.key_blocks.get(name + '.R')
    if left_shape and right_shape:
        obj.shape_key_remove(left_shape)
        obj.shape_key_remove(right_shape)


def reload_physic_objects():
    if not physic_objects.is_enable():
        return

    bones = bpy.context.active_object.pose.bones

    physic_objects.clear()
    for bone in bones:
        if not bone.physic_bind.is_enable: continue
        target = bones[bone.physic_bind.target]
 
        physic_objects.add_object(FollowObject(
            obj=bone,
            target=target
        ))


# def my_handler(scene):
#     physic_objects.update()


class PhysicBind(bpy.types.PropertyGroup):
    is_enable: bpy.props.BoolProperty(name='Enable Physic')
    target: bpy.props.StringProperty(name="")


class ShapeKeyLR(bpy.types.PropertyGroup):
    left: bpy.props.StringProperty(name='Left Group')
    right: bpy.props.StringProperty(name='Right Group')


class PhysicFollowSettings(bpy.types.PropertyGroup):
    speed: bpy.props.FloatProperty(soft_min=.05, soft_max=1, default=.2, name='Speed')
    velocity: bpy.props.FloatProperty(soft_min=.05, soft_max=1, default=.9, name='Velocity')
    noise_enable: bpy.props.BoolProperty(default=False, name='Noise')
    only_velocity: bpy.props.BoolProperty(default=False, name='Only Velocity')
    noise_coords: bpy.props.BoolVectorProperty(name='', default=[True, True, True], subtype='XYZ')
    noise_strange: bpy.props.FloatProperty(soft_min=.0, soft_max=1, default=.2, name='Noise Strange')
    noise_rate: bpy.props.FloatProperty(soft_min=.05, soft_max=1, default=.05, name='Noise Rate', step=.01)


class ZENU_OT_start_physic(bpy.types.Operator):
    bl_label = 'Start'
    bl_idname = 'zenu.start_physic'
    bl_options = {"UNDO"}

    def execute(self, context: Context):
        physic_objects.toggle()
        reload_physic_objects()
        return {'FINISHED'}


class ZENU_OT_create_shape_key_left_right_remove(bpy.types.Operator):
    bl_label = 'Create Left Right Shape Key Remove'
    bl_idname = 'zenu.create_shape_key_left_right_remove'
    bl_options = {"UNDO"}

    def execute(self, context: Context):
        obj = bpy.context.active_object
        remove_lr_shapes(obj, obj.active_shape_key.name)
        return {'FINISHED'}


class ZENU_OT_create_shape_key_left_right(bpy.types.Operator):
    bl_label = 'Create Left Right Shape Key'
    bl_idname = 'zenu.create_shape_key_left_right'
    bl_options = {"UNDO"}

    def execute(self, context: Context):
        lr = context.active_object.shape_key_lr
        obj = bpy.context.active_object
        shape_key = obj.active_shape_key
        prev = obj.show_only_shape_key

        remove_lr_shapes(obj, obj.active_shape_key.name)

        obj.show_only_shape_key = True
        left_shape = obj.shape_key_add(name=shape_key.name + '.L', from_mix=True)
        right_shape = obj.shape_key_add(name=shape_key.name + '.R', from_mix=True)
        obj.show_only_shape_key = prev

        left_shape.vertex_group = lr.left
        right_shape.vertex_group = lr.right

        return {'FINISHED'}


class ZENU_OT_bind_physic_to_active(bpy.types.Operator):
    bl_label = 'Bind Physic To Active'
    bl_idname = 'zenu.bind_physic_to_active'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return check_mods('p')

    def execute(self, context: Context):
        active = context.active_pose_bone
        to_bind = context.selected_pose_bones.copy()
        to_bind.remove(active)

        for i in to_bind:
            i.physic_bind.is_enable = True
            i.physic_bind.target = active.name

        reload_physic_objects()
        return {'FINISHED'}


class ZENU_PT_phyisc(BasePanel):
    bl_label = 'Physic'
    bl_context = ''

    def draw(self, context: Context):
        layout = self.layout

        col = layout.column_flow(align=True)
        col.operator(ZENU_OT_create_shape_key_left_right.bl_idname)
        col.operator(ZENU_OT_create_shape_key_left_right_remove.bl_idname)
        lr = context.active_object.shape_key_lr
        col.prop_search(lr, 'left', context.active_object, 'vertex_groups')
        col.prop_search(lr, 'right', context.active_object, 'vertex_groups')

        active = context.active_pose_bone

        if active is None:
            return

        armature: bpy.types.Armature = context.active_object.data

        physic_bind = active.physic_bind
        follow_settings = active.follow_settings

        col = layout.column_flow(align=True)
        col.operator(ZENU_OT_start_physic.bl_idname, depress=physic_objects.is_enable())

        col = layout.column_flow(align=True)
        col.prop(physic_bind, 'is_enable', icon='CHECKBOX_HLT')

        if not physic_bind.is_enable:
            return

        col.prop_search(physic_bind, 'target', armature, 'bones')
        col.prop(follow_settings, 'only_velocity', toggle=True)
        col.prop(follow_settings, 'velocity')
        col.prop(follow_settings, 'speed')

        col = layout.column_flow(align=True)
        col.prop(follow_settings, 'noise_enable', icon='CHECKBOX_HLT')
        if follow_settings.noise_enable:
            col.row(align=True).prop(follow_settings, 'noise_coords', toggle=True)
            col.prop(follow_settings, 'noise_strange')
            col.prop(follow_settings, 'noise_rate')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_phyisc,
    ZENU_OT_start_physic,
    PhysicBind,
    ShapeKeyLR,
    PhysicFollowSettings,
    ZENU_OT_bind_physic_to_active,
    ZENU_OT_create_shape_key_left_right,
    ZENU_OT_create_shape_key_left_right_remove
))


def register():
    reg()
    bpy.types.Object.shape_key_lr = bpy.props.PointerProperty(type=ShapeKeyLR)
    bpy.types.PoseBone.physic_bind = bpy.props.PointerProperty(type=PhysicBind)
    bpy.types.PoseBone.follow_settings = bpy.props.PointerProperty(type=PhysicFollowSettings)


def unregister():
    unreg()
    physic_objects.stop()

import json

import bpy


class ZChainCollection(bpy.types.PropertyGroup):
    stiffness: bpy.props.FloatProperty(default=100)
    damping: bpy.props.FloatProperty(default=10)

    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    bone: bpy.props.StringProperty()
    constraints: bpy.props.StringProperty(default='{}')


class ZENU_OT_chain_bone_action(bpy.types.Operator):
    bl_label = 'Chain Bone Action'
    bl_idname = 'zenu.chain_bone_action'
    bl_options = {'UNDO'}
    action: bpy.props.EnumProperty(items=(
        ('SELECT', '', ''),
        ('DELETE', '', ''),
    ))
    bone: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        coll: ZChainCollection = scene.zenu_physic_chain_collection[scene.zenu_physic_chain_collection_active]
        obj: bpy.types.Object = coll.obj

        if self.action == 'SELECT':
            bpy.ops.pose.select_all(action='DESELECT')
            bone = obj.data.bones[self.bone]
            bone.select = True

        return {'FINISHED'}


class ZENU_OT_chain_action(bpy.types.Operator):
    bl_label = 'Chain Action'
    bl_idname = 'zenu.chain_active_action'
    bl_options = {'UNDO'}
    action: bpy.props.EnumProperty(items=(
        ('ADD_ROOT', '', ''),
        ('ADD_CHAIN', '', ''),
        ('CLEAR', '', ''),
    ))

    def add_root(self, arm: bpy.types.Object, bone: bpy.types.PoseBone):
        context = bpy.context
        coll: ZChainCollection = None

        for i in context.scene.zenu_physic_chain_collection:
            if i.obj == arm and i.bone == bone.name:
                coll = i
                break

        if coll is None:
            coll = context.scene.zenu_physic_chain_collection.add()
            coll.obj = arm
            coll.bone = bone.name
            self.add_bone_to_chain(bone, coll)

        return coll

    def add_bone_to_chain(self, bone: bpy.types.PoseBone, coll: ZChainCollection = None):
        context = bpy.context
        if coll is None:
            coll = context.scene.zenu_physic_chain_collection[
                context.scene.zenu_physic_chain_collection_active]

        coll.constraints = json.dumps({**json.loads(coll.constraints), bone.name: {}})

    def execute(self, context: bpy.types.Context):
        bone = context.active_pose_bone
        if self.action == 'ADD_ROOT':
            self.add_root(context.active_object, bone)
        elif self.action == 'CLEAR':
            context.scene.zenu_physic_chain_collection.clear()
        elif self.action == 'ADD_CHAIN':
            self.add_bone_to_chain(bone)

        return {'FINISHED'}


class ZENU_UL_chain_collection(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        col = layout.column()
        col.label(text=f'{item.obj.name} -> {item.bone}')


def draw(context: bpy.types.Context, layout: bpy.types.UILayout):
    scene = context.scene

    layout.template_list('ZENU_UL_chain_collection', '',
                         scene, 'zenu_physic_chain_collection',
                         scene, 'zenu_physic_chain_collection_active')

    try:
        coll = scene.zenu_physic_chain_collection[scene.zenu_physic_chain_collection_active]
        col = layout.column(align=True)
        col.prop(coll, 'stiffness')
        col.prop(coll, 'damping')

        col = layout.column(align=True)
        for i in json.loads(coll.constraints).keys():
            row = col.row(align=True)
            row.scale_y = 1.2

            bone_action = row.operator(ZENU_OT_chain_bone_action.bl_idname, text='', icon='TRASH')
            bone_action.action = 'DELETE'
            bone_action.bone = i

            bone_action = row.operator(ZENU_OT_chain_bone_action.bl_idname, text=i)
            bone_action.action = 'SELECT'
            bone_action.bone = i
    except IndexError:
        pass

    col = layout.row(align=True)
    add_root = col.operator(ZENU_OT_chain_action.bl_idname, text='Add Root')
    add_root.action = 'ADD_ROOT'

    add_root = col.operator(ZENU_OT_chain_action.bl_idname, text='Add Chain')
    add_root.action = 'ADD_CHAIN'

    clear = layout.operator(ZENU_OT_chain_action.bl_idname, text='Clear')
    clear.action = 'CLEAR'


reg, unreg = bpy.utils.register_classes_factory((
    ZChainCollection,
    ZENU_UL_chain_collection,
    ZENU_OT_chain_action,
    ZENU_OT_chain_bone_action
))


def register():
    reg()
    bpy.types.Scene.zenu_physic_chain_collection = bpy.props.CollectionProperty(type=ZChainCollection)
    bpy.types.Scene.zenu_physic_chain_collection_active = bpy.props.IntProperty()


def unregister():
    unreg()

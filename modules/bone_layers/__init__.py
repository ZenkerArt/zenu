import bpy
from ...base_panel import BasePanel


class ArmatureLayer(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    obj: bpy.props.PointerProperty(type=bpy.types.Object)


class ZENU_UL_armature_layers(bpy.types.UIList):
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data, item: ArmatureLayer, icon, active_data, active_propname):
        obj: bpy.types.Object = item.obj
        layout.prop(item, 'name', text='', emboss=False)

        op = layout.operator(
            operator=ZENU_OT_armature_layer_item_action.bl_idname,
            text='',
            icon='RADIOBUT_ON' if obj.select_get() else 'RADIOBUT_OFF',
            emboss=False
        )
        op.action = 'TOGGLE_SELECTION'
        op.obj_name = obj.name

        op = layout.operator(
            operator=ZENU_OT_armature_layer_item_action.bl_idname,
            text='',
            icon='HIDE_ON' if obj.hide_get() else 'HIDE_OFF',
            emboss=False
        )
        op.action = 'TOGGLE_HIDE'

        op.obj_name = item.obj.name


class ZENU_OT_armature_layer_action(bpy.types.Operator):
    bl_label = 'Armature Layer Action'
    bl_idname = 'zenu.armature_layer_action'

    action: bpy.props.EnumProperty(items=(
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
        ('UP', 'Up', ''),
        ('DOWN', 'Down', ''),
    ))

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        layers: bpy.types.CollectionProperty = scene.zenu_armature_layers
        layers_active: int = scene.zenu_armature_layers_active

        if self.action == 'ADD':
            item: ArmatureLayer = layers.add()
            item.obj = context.active_object
            item.name = item.obj.name
        elif self.action == 'REMOVE':
            layers.remove(layers_active)
        elif self.action == 'UP':
            layers.move(layers_active, layers_active - 1)
            scene.zenu_armature_layers_active = layers_active - 1
        elif self.action == 'DOWN':
            layers.move(layers_active, layers_active + 1)
            scene.zenu_armature_layers_active = layers_active + 1

        return {'FINISHED'}


class ZENU_OT_armature_layer_item_action(bpy.types.Operator):
    bl_label = 'Armature Layer Item Action'
    bl_idname = 'zenu.armature_layer_item_action'

    action: bpy.props.EnumProperty(items=(
        ('TOGGLE_SELECTION', 'Toggle Selection', ''),
        ('TOGGLE_HIDE', 'Toggle Hide', ''),
    ))

    obj_name: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        layers: bpy.types.CollectionProperty = scene.zenu_armature_layers
        obj = bpy.data.objects[self.obj_name]

        if self.action == 'TOGGLE_SELECTION':
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(not obj.select_get())
            bpy.ops.object.mode_set(mode='POSE')
        elif self.action == 'TOGGLE_HIDE':
            obj.hide_set(not obj.hide_get())

        return {'FINISHED'}


class ZENU_PT_bone_layer(BasePanel):
    bl_label = 'Bone UI'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list('ZENU_UL_armature_layers', '',
                          scene, 'zenu_armature_layers',
                          scene, 'zenu_armature_layers_active')

        col = row.column(align=True)
        op = col.operator(
            ZENU_OT_armature_layer_action.bl_idname,
            icon='ADD',
            text=''
        )
        op.action = 'ADD'

        op = col.operator(
            ZENU_OT_armature_layer_action.bl_idname,
            icon='REMOVE',
            text=''
        )
        op.action = 'REMOVE'

        col = row.column(align=True)
        op = col.operator(
            ZENU_OT_armature_layer_action.bl_idname,
            icon='TRIA_UP',
            text=''
        )
        op.action = 'UP'

        op = col.operator(
            ZENU_OT_armature_layer_action.bl_idname,
            icon='TRIA_DOWN',
            text=''
        )
        op.action = 'DOWN'

        layout.template_bone_collection_tree()
        # layout.col
        # layout.active


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_bone_layer,
    ZENU_UL_armature_layers,
    ZENU_OT_armature_layer_action,
    ZENU_OT_armature_layer_item_action,
    ArmatureLayer
))


def on_change_update(self, context):
    scene = context.scene

    layers: bpy.types.CollectionProperty = scene.zenu_armature_layers
    layers_active: int = scene.zenu_armature_layers_active
    arm: ArmatureLayer = layers[layers_active]

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.obj.select_set(True)

    bpy.context.view_layer.objects.active = arm.obj
    bpy.ops.object.mode_set(mode='POSE')
    # print(arm.obj)


def register():
    reg()
    bpy.types.Scene.zenu_armature_layers = bpy.props.CollectionProperty(
        type=ArmatureLayer)
    bpy.types.Scene.zenu_armature_layers_active = bpy.props.IntProperty(
        update=on_change_update)


def unregister():
    unreg()

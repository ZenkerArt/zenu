import bpy
from ...base_panel import BasePanel
from ...utils import get_modifier


def open_scene(scene: str | bpy.types.Scene):
    if isinstance(scene, str):
        scene = bpy.data.scenes[scene]

    bpy.context.window.scene = scene


class ZENU_OT_open_scene(bpy.types.Operator):
    bl_label = 'Open Scene'
    bl_idname = 'zenu.open_scene'
    scene: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        open_scene(self.scene)
        return {'FINISHED'}


class ZENU_OT_remove_scene(bpy.types.Operator):
    bl_label = 'Remove Scene'
    bl_idname = 'zenu.remove_scene'
    bl_options = {'UNDO'}
    scene: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        scene = bpy.data.scenes[self.scene]
        bpy.data.scenes.remove(scene)
        return {'FINISHED'}


class ZENU_OT_move_selected_to_scene(bpy.types.Operator):
    bl_label = 'Move Selected To Scene'
    bl_idname = 'zenu.move_selected_to_scene'
    bl_options = {'UNDO'}
    scene: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        scene = bpy.data.scenes[self.scene]
        for obj in context.selected_objects:
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
            scene.collection.objects.link(obj)

        open_scene(scene)
        return {'FINISHED'}


class ZENU_OT_move_collection_to_scene(bpy.types.Operator):
    bl_label = 'Move Collection To Scene'
    bl_idname = 'zenu.move_collection_to_scene'
    bl_options = {'UNDO'}
    scene: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        scene = bpy.data.scenes[self.scene]
        # bpy.ops.outliner.id_operation(type='UNLINK')
        scene.collection.children.link(context.collection)
        return {'FINISHED'}


class ZENU_UL_scene_select(bpy.types.UIList):
    def draw_item(self, context: bpy.types.Context, layout, data, item: bpy.types.Scene, icon, active_data,
                  active_propname):
        layout.prop(item, 'name', emboss=False, text='')

        col = layout.row(align=True)

        op = col.operator(ZENU_OT_open_scene.bl_idname, text='',
                          icon='HIDE_OFF' if context.scene == item else 'HIDE_ON', emboss=False)
        op.scene = item.name

        op = col.operator(ZENU_OT_remove_scene.bl_idname, text='', icon='X', emboss=False)
        op.scene = item.name


class ZENU_PT_scene_manager(BasePanel):
    bl_label = 'Scene Manager'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.template_list('ZENU_UL_scene_select', '',
                             bpy.data, 'scenes',
                             context.scene, 'zenu_scene_select')

        selected_scene: bpy.types.Scene = bpy.data.scenes[context.scene.zenu_scene_select]

        layout.operator('scene.new')
        op = layout.operator(ZENU_OT_move_collection_to_scene.bl_idname)
        op.scene = selected_scene.name
        op = layout.operator(ZENU_OT_move_selected_to_scene.bl_idname)
        op.scene = selected_scene.name

        op = layout.operator(ZENU_OT_open_scene.bl_idname)
        op.scene = selected_scene.name


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_open_scene,
    ZENU_OT_remove_scene,
    ZENU_OT_move_selected_to_scene,
    ZENU_OT_move_collection_to_scene,
    ZENU_PT_scene_manager,
    ZENU_UL_scene_select,
))


def register():
    bpy.types.Scene.zenu_scene_select = bpy.props.IntProperty()
    reg()


def unregister():
    unreg()

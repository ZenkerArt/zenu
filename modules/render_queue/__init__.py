import os

import bpy
from bpy_extras.io_utils import ImportHelper
from ...base_panel import BasePanel


class RenderQueue(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='Unknown')
    path: bpy.props.StringProperty()


class ZENU_UL_render_queue(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        col = layout.column()
        col.label(text=f'{item.name}')


class ZENU_OT_add_render_queue(bpy.types.Operator, ImportHelper):
    bl_idname = "zenu.add_render_queue"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Add Render Queue"
    bl_options = {'UNDO'}
    # ImportHelper mixin class uses this
    filename_ext = ".blend"

    filter_glob: bpy.props.StringProperty(
        default="*.blend;",
        options={'HIDDEN'},
    )

    filename: bpy.props.StringProperty(maxlen=1024)
    directory: bpy.props.StringProperty(maxlen=1024)

    # files: bpy.props.CollectionProperty(name='File paths', type=bpy.types.OperatorFileListElement)

    def execute(self, context):
        f = os.path.join(self.directory, self.filename)
        file = context.scene.zenu_render_queue.add()

        file.name = self.filename
        file.path = bpy.path.relpath(f)

        return {'FINISHED'}


class ZENU_OT_render_queue_action(bpy.types.Operator):
    bl_label = 'Render Queue Action'
    bl_idname = 'zenu.render_queue_action'
    action: bpy.props.EnumProperty(items=(
        ('REMOVE', 'Remove', ''),
    ))

    def execute(self, context: bpy.types.Context):
        action = self.action

        if action == 'REMOVE':
            context.scene.zenu_render_queue.remove(context.scene.zenu_render_queue_active)
        return {'FINISHED'}


class ZENU_PT_render_queue(BasePanel):
    bl_label = 'Render Queue'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        layout.template_list('ZENU_UL_render_queue', '',
                             scene, 'zenu_render_queue',
                             scene, 'zenu_render_queue_active')

        layout.operator(ZENU_OT_add_render_queue.bl_idname)

        op = layout.operator(ZENU_OT_render_queue_action.bl_idname)
        op.action = 'REMOVE'

        try:
            data = context.scene.zenu_render_queue[context.scene.zenu_render_queue_active]
            layout.prop(data, 'path', text='')
        except IndexError:
            pass


reg, unreg = bpy.utils.register_classes_factory((
    RenderQueue,
    ZENU_OT_render_queue_action,
    ZENU_OT_add_render_queue,
    ZENU_UL_render_queue,
    ZENU_PT_render_queue,
))


def register():
    reg()
    bpy.types.Scene.zenu_render_queue = bpy.props.CollectionProperty(type=RenderQueue)
    bpy.types.Scene.zenu_render_queue_active = bpy.props.IntProperty()


def unregister():
    unreg()

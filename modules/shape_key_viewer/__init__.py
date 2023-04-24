import bpy
from bpy.types import Context
from .shape_key_list import ZENU_UL_shape_key_list
from ...base_panel import BasePanel
from ...utils import check_mods


class ZENU_OT_shape_keys_action(bpy.types.Operator):
    bl_label = 'Shape Key Action'
    bl_idname = 'zenu.shape_key_action'
    obj: bpy.props.StringProperty()
    action: bpy.props.EnumProperty(items=[
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
        ('UP', 'up', ''),
        ('DOWN', 'down', ''),
    ])

    def execute(self, context: Context):
        if not self.obj:
            return {'FINISHED'}

        override = bpy.context.copy()
        override['object'] = bpy.data.objects[self.obj]

        match self.action:
            case 'ADD':
                bpy.ops.object.shape_key_add(override, from_mix=False)
            case 'REMOVE':
                bpy.ops.object.shape_key_remove(override, all=False)
            case 'UP':
                bpy.ops.object.shape_key_move(override, type='UP')
            case 'DOWN':
                bpy.ops.object.shape_key_move(override, type='DOWN')
        return {'FINISHED'}


class ZENU_PT_shape_key_viewer(BasePanel):
    bl_label = 'Shape Key Viewer'
    bl_context = ''

    @classmethod
    def poll(cls, context: Context):
        return check_mods('oepws')

    @staticmethod
    def get_object(context: Context):
        obj = context.active_object

        if context.scene.shape_key_pin:
            obj = context.scene.shape_key_pin

        if obj is None:
            return

        if not isinstance(obj.data, bpy.types.Mesh):
            return

        if obj.data.shape_keys is None:
            return

        return obj

    def draw_list(self, obj: bpy.types.Object):
        layout = self.layout
        row = layout.row()
        row.template_list('ZENU_UL_shape_key_list', '', obj.data.shape_keys,
                          'key_blocks', obj,
                          'active_shape_key_index')

        col = row.column(align=True)
        op = col.operator(ZENU_OT_shape_keys_action.bl_idname, icon='ADD', text="")
        op.action = 'ADD'
        op.obj = obj.name

        op = col.operator(ZENU_OT_shape_keys_action.bl_idname, icon='REMOVE', text="")
        op.action = 'REMOVE'
        op.obj = obj.name
        col.separator()

        op = col.operator(ZENU_OT_shape_keys_action.bl_idname, icon='TRIA_UP', text="")
        op.action = 'UP'
        op.obj = obj.name

        op = col.operator(ZENU_OT_shape_keys_action.bl_idname, icon='TRIA_DOWN', text="")
        op.action = 'DOWN'
        op.obj = obj.name

    def draw(self, context: Context):
        layout = self.layout
        obj = self.get_object(context)

        if obj is None:
            if context.scene.shape_key_pin:
                self.draw_toggle(context.scene,
                                 'shape_key_is_pin',
                                 text='Pin Object',
                                 on_icon='PINNED',
                                 off_icon='UNPINNED',
                                 )
            layout.label(text='Not found object')
            return

        col = layout.column_flow(align=True)
        self.draw_toggle(context.scene,
                         'shape_key_is_pin',
                         text='Pin Object',
                         on_icon='PINNED',
                         off_icon='UNPINNED',
                         layout=col,
                         )

        if context.scene.shape_key_pin:
            col.prop(context.scene, 'shape_key_pin', text='')

        self.draw_list(obj)
        layout.prop(obj, 'show_only_shape_key')


def update_pin_shape_key(self, context):
    toggle: bool = self.shape_key_is_pin
    if toggle and context.active_object.data.shape_keys is not None:
        context.scene.shape_key_pin = context.active_object
    else:
        context.scene.shape_key_pin = None


def zenu_depsgraph_update_post(self, change):
    if self.shape_key_pin is None:
        self.shape_key_is_pin = False
        return

    try:
        self.shape_key_pin.data
        if self.shape_key_pin.data.shape_keys is None:
            self.shape_key_is_pin = False
    except ReferenceError:
        self.shape_key_is_pin = False


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_shape_key_viewer,
    ZENU_UL_shape_key_list,
    ZENU_OT_shape_keys_action
))


def scene_pin_object_poll(self, obj):
    return obj.type == 'MESH' and obj.data.shape_keys is not None


def register():
    bpy.types.Scene.shape_key_is_pin = bpy.props.BoolProperty(update=update_pin_shape_key, default=False)
    bpy.types.Scene.shape_key_pin = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=scene_pin_object_poll
    )
    reg()
    if zenu_depsgraph_update_post not in bpy.app.handlers:
        bpy.app.handlers.depsgraph_update_post.append(zenu_depsgraph_update_post)


def unregister():
    unreg()
    try:
        bpy.app.handlers.depsgraph_update_post.remove(zenu_depsgraph_update_post)
    except ValueError:
        pass

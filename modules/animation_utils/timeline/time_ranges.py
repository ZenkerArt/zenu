import bpy
from ....base_panel import BasePanel


class ZENU_UL_time_ranges(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: 'TimeRange', icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')
        layout.label(text=f'{item.start}/{item.end}')


class TimeRange(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    start: bpy.props.IntProperty()
    end: bpy.props.IntProperty()


def get_time_ranges(context: bpy.types.Context) -> list[TimeRange]:
    return context.scene.zenu_time_ranges


def get_active_range(context: bpy.types.Context) -> TimeRange:
    return context.scene.zenu_time_ranges[context.scene.zenu_time_ranges_active]


def add_time_range(context: bpy.types.Context, name: str) -> TimeRange:
    item = get_time_ranges(context).add()
    item.name = name
    return item


def add_or_get_time_range(context: bpy.types.Context, name: str) -> TimeRange:
    for i in get_time_ranges(context):
        if i.name == name:
            return i

    item = get_time_ranges(context).add()
    item.name = name
    return item


def apply_time_range(time_range: TimeRange):
    bpy.context.scene.frame_preview_start = time_range.start
    bpy.context.scene.frame_preview_end = time_range.end


class ZENU_OT_range_action(bpy.types.Operator):
    bl_label = 'Add Range'
    bl_idname = 'zenu.add_range'
    options = {'UNDO_GROUP'}
    action: bpy.props.EnumProperty(items=(
        ('ADD', '', 'Add'),
        ('UPDATE', '', 'Update'),
        ('APPLY', '', 'Apply'),
        ('REMOVE', '', 'Remove'),
    ))

    def execute(self, context: bpy.types.Context):
        time_range = None

        try:
            time_range = get_active_range(context)
        except IndexError:
            pass
        ranges = get_time_ranges(context)

        match self.action:
            case 'ADD':
                time_range = add_time_range(context, 'None')
                time_range.start = context.scene.frame_preview_start
                time_range.end = context.scene.frame_preview_end
            case 'UPDATE':
                time_range.start = context.scene.frame_preview_start
                time_range.end = context.scene.frame_preview_end
            case 'APPLY':
                apply_time_range(time_range)
            case 'REMOVE':
                ranges.remove(context.scene.zenu_time_ranges_active)
        return {'FINISHED'}


class ZENU_PT_time_ranges(BasePanel):
    bl_label = 'Time Ranges'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        layout.template_list('ZENU_UL_time_ranges', '',
                             context.scene, 'zenu_time_ranges',
                             context.scene, 'zenu_time_ranges_active')

        op = layout.operator(ZENU_OT_range_action.bl_idname, text='Apply Range')
        op.action = 'APPLY'

        col = layout.column(align=True)
        op = col.operator(ZENU_OT_range_action.bl_idname)
        op.action = 'ADD'
        op = col.operator(ZENU_OT_range_action.bl_idname, text='Update Range')
        op.action = 'UPDATE'
        op = col.operator(ZENU_OT_range_action.bl_idname, text='Remove Range')
        op.action = 'REMOVE'


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_time_ranges,
    ZENU_UL_time_ranges,
    ZENU_OT_range_action,
    TimeRange,
))


def register():
    reg()
    bpy.types.Scene.zenu_time_ranges = bpy.props.CollectionProperty(type=TimeRange)
    bpy.types.Scene.zenu_time_ranges_active = bpy.props.IntProperty()


def unregister():
    unreg()

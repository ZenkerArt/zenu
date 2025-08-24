import bpy
from ....utils import exit_from_nla
from ..timeline.time_ranges import add_or_get_time_range, apply_time_range
from ...menu_manager import menu_timeline
from ....base_panel import BasePanel

TIME_RANGE_NAME = 'Edit Loop Last Range'

class ZENU_UL_nla_loops(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        row = layout.row(align=True)
        if item.action:
            layout.prop(item.action, 'name', emboss=False, text='')
        elif not item.name:
            layout.label(text='None')
        else:
            layout.prop(item, 'name', emboss=False, text='')


class LoopInfo(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    run: bpy.props.StringProperty()
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    disable_strips: bpy.props.BoolProperty(default=True)
    start: bpy.props.IntProperty(name='Start')
    end: bpy.props.IntProperty(name='End')


def add_nla(context: bpy.types.Context, strip: bpy.types.NlaStrip) -> LoopInfo:
    for i in context.scene.zenu_nla_loops:
        i: LoopInfo

        try:
            if i.action.name == strip.action.name:
                return i
        except Exception as e:
            print(e)

    item = context.scene.zenu_nla_loops.add()

    item.name = strip.action.name
    item.action = strip.action
    item.obj = strip.id_data

    item.start_offset = int(strip.action_frame_start)
    item.end_offset = int(strip.action_frame_end)
    return item


class ZENU_OT_nla_add_loop(bpy.types.Operator):
    bl_label = 'Add Loop'
    bl_idname = 'zenu.add_loop'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        for strip in context.selected_nla_strips:
            add_nla(context, strip)

        return {'FINISHED'}


class ZENU_OT_nla_add_loop_group(bpy.types.Operator):
    bl_label = 'Add Loop Group'
    bl_idname = 'zenu.add_loop_group'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        items: list[LoopInfo] = []

        for strip in context.selected_nla_strips:
            items.append(add_nla(context, strip))

        item = context.scene.zenu_nla_loops.add()
        item.name = 'RunLoop'
        item.run = ','.join({i.name for i in items})

        return {'FINISHED'}


class ZENU_OT_nla_exit_loop(bpy.types.Operator):
    bl_label = 'Exit Loop'
    bl_idname = 'zenu.exit_loop'
    bl_options = {'UNDO'}

    def exit(self, loop: LoopInfo):
        obj: bpy.types.Object = loop.obj
        action = loop.action
        if loop.disable_strips:
            for track in obj.animation_data.nla_tracks:
                for i in track.strips:
                    if i.action != action: continue
                    i.mute = False
        obj.animation_data.action = None

    def execute(self, context: bpy.types.Context):
        loop: LoopInfo = context.scene.zenu_nla_loops[context.active_object.zenu_nla_loops_active]
        apply_time_range(add_or_get_time_range(context, TIME_RANGE_NAME))
        context.scene.use_preview_range = context.scene.zenu_nla_loops_active_preview

        if loop.run:
            for i in loop.run.replace(' ', '').split(','):
                self.exit(context.scene.zenu_nla_loops[i])

            return {'FINISHED'}
        self.exit(loop)
        return {'FINISHED'}


class ZENU_OT_nla_edit_loop(bpy.types.Operator):
    bl_label = 'Edit Loop'
    bl_idname = 'zenu.edit_loop'
    bl_options = {'UNDO'}

    def edit(self, loop: LoopInfo):
        obj: bpy.types.Object = loop.obj
        exit_from_nla(obj)

        action: bpy.types.Action = loop.action
        obj.select_set(True)
        if loop.disable_strips:
            for track in obj.animation_data.nla_tracks:
                for i in track.strips:
                    if i.action != action: continue
                    i.mute = True
        bpy.context.scene.use_preview_range = True
        bpy.context.scene.frame_preview_start = loop.start
        bpy.context.scene.frame_preview_end = loop.end

        obj.animation_data.action = action

    def execute(self, context: bpy.types.Context):
        loop: LoopInfo = context.scene.zenu_nla_loops[context.active_object.zenu_nla_loops_active]
        context.scene.zenu_nla_loops_active_preview = context.scene.use_preview_range
        time_range = add_or_get_time_range(context, name=TIME_RANGE_NAME)
        time_range.start = context.scene.frame_preview_start
        time_range.end = context.scene.frame_preview_end

        if loop.run:
            for i in loop.run.replace(' ', '').split(','):
                self.edit(context.scene.zenu_nla_loops[i])

            return {'FINISHED'}
        self.edit(loop)
        return {'FINISHED'}


class ZENU_OT_nla_loop_remove(bpy.types.Operator):
    bl_label = 'Remove Loop'
    bl_idname = 'zenu.nla_loop_remove'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        context.scene.zenu_nla_loops.remove(context.active_object.zenu_nla_loops_active)
        return {'FINISHED'}


class ZENU_PT_animation_nla_loop(BasePanel):
    bl_label = 'NLA Loops'
    bl_space_type = 'NLA_EDITOR'

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        if context.active_object is None:
            return 

        layout.template_list('ZENU_UL_nla_loops', '',
                             context.scene, 'zenu_nla_loops',
                             context.active_object, 'zenu_nla_loops_active')

        col = layout.column(align=True)
        # col.scale_y = 1.5
        col.operator(ZENU_OT_nla_add_loop.bl_idname)
        col.operator(ZENU_OT_nla_add_loop_group.bl_idname)
        col.operator(ZENU_OT_nla_loop_remove.bl_idname)

        col = layout.column(align=True)
        col.scale_y = 1.5
        col.operator(ZENU_OT_nla_edit_loop.bl_idname)
        col.operator(ZENU_OT_nla_exit_loop.bl_idname)

        try:
            loop = context.scene.zenu_nla_loops[context.active_object.zenu_nla_loops_active]
        except IndexError:
            return
        col = layout.column(align=True)
        col.prop(loop, 'obj', text='')
        col.prop(loop, 'action', text='')
        col = layout.column(align=True)
        # col.scale_y = 1.5
        # col.prop(loop, 'start')
        # col.prop(loop, 'end')
        #
        # col = layout.column(align=True)
        # col.prop(loop, 'disable_strips')
        # col.prop(loop, 'name')
        # col.prop(loop, 'run')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_animation_nla_loop,
    ZENU_UL_nla_loops,
    ZENU_OT_nla_edit_loop,
    ZENU_OT_nla_add_loop,
    ZENU_OT_nla_add_loop_group,
    ZENU_OT_nla_exit_loop,
    ZENU_OT_nla_loop_remove,
    LoopInfo,
))


def register():
    reg()
    menu_timeline.down.add(ZENU_OT_nla_edit_loop.bl_idname)
    menu_timeline.down.add(ZENU_OT_nla_exit_loop.bl_idname)
    bpy.types.Scene.zenu_nla_loops = bpy.props.CollectionProperty(type=LoopInfo)
    bpy.types.Object.zenu_nla_loops_active = bpy.props.IntProperty()
    bpy.types.Scene.zenu_nla_loops_active_preview = bpy.props.BoolProperty()


def unregister():
    unreg()

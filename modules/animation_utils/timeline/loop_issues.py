import bpy
from ....base_panel import BasePanel


def get_loop_issue_props(context: bpy.types.Context) -> 'LoopIssuesProps':
    return context.scene.zenu_loop_issues_props


def get_loop_issues(context: bpy.types.Context) -> list['LoopIssue']:
    return context.scene.zenu_loop_issues


class ZENU_UL_nla_loop_issues(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')


class LoopIssuesProps(bpy.types.PropertyGroup):
    loop_count_from_range: bpy.props.BoolProperty(name='Manual Range')
    loop_count: bpy.props.IntProperty(name='Loop Count')


class LoopIssue(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    data_path: bpy.props.StringProperty()
    index: bpy.props.IntProperty()


class ZENU_OT_analyze_loop(bpy.types.Operator):
    bl_label = 'Analyze'
    bl_idname = 'zenu.analyze_loop'

    frame_count: bpy.props.FloatProperty(default=0)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        try:
            anim_data = obj.animation_data
            action = anim_data.action
        except AttributeError:
            return {'CANCELED'}

        issues = get_loop_issues(context)
        issues.clear()

        for i in action.fcurves:
            start_key = i.keyframe_points[0]
            end_key = i.keyframe_points[-1]
            t = end_key.co_ui.x - start_key.co_ui.x
            y = end_key.co_ui.y - start_key.co_ui.y

            if abs(y) > .0000001:
                item = issues.add()
                item.name = f'Difference Value Curve'
                item.data_path = i.data_path
                item.index = i.array_index

            if t != self.frame_count:
                item = issues.add()
                item.name = f'!= {self.frame_count}'
                item.data_path = i.data_path
                item.index = i.array_index

        return {'FINISHED'}


class ZENU_OT_select_issue(bpy.types.Operator):
    bl_label = 'Select'
    bl_idname = 'zenu.select_issue'

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        try:
            anim_data = obj.animation_data
            action = anim_data.action
        except AttributeError:
            return {'CANCELED'}

        active_index = context.scene.zenu_loop_issues_active
        issues = get_loop_issues(context)

        try:
            issue = issues[active_index]
        except IndexError:
            return {'CANCELED'}

        fcurve = action.fcurves.find(issue.data_path, index=issue.index)

        if fcurve is None:
            return {'CANCELED'}

        fcurve.select = True
        for key in fcurve.keyframe_points:
            key.select_control_point = True

        return {'FINISHED'}


def draw(self: 'ZENU_PT_loop_issues_de', context: bpy.types.Context):
    settings: LoopIssuesProps = get_loop_issue_props(context)
    layout = self.layout

    col = layout.column(align=True)
    col.prop(settings, 'loop_count_from_range', icon='ARROW_LEFTRIGHT')
    if settings.loop_count_from_range:
        col.prop(settings, 'loop_count')

    layout.template_list('ZENU_UL_nla_loop_issues', '',
                         context.scene, 'zenu_loop_issues',
                         context.scene, 'zenu_loop_issues_active')

    col = layout.column(align=True)
    op = col.operator(ZENU_OT_select_issue.bl_idname)
    op = col.operator(ZENU_OT_analyze_loop.bl_idname)

    issue_props = get_loop_issue_props(context)

    op.frame_count = issue_props.loop_count
    if not issue_props.loop_count_from_range:
        op.frame_count = context.scene.frame_preview_end - context.scene.frame_preview_start


class ZENU_PT_loop_issues_de(BasePanel):
    bl_label = 'Loop Issues'
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


class ZENU_PT_loop_issues_ge(BasePanel):
    bl_label = 'Loop Issues'
    bl_space_type = 'GRAPH_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_UL_nla_loop_issues,
    ZENU_PT_loop_issues_de,
    ZENU_PT_loop_issues_ge,
    ZENU_OT_analyze_loop,
    ZENU_OT_select_issue,
    LoopIssuesProps,
    LoopIssue
))


def register():
    reg()
    bpy.types.Scene.zenu_loop_issues_props = bpy.props.PointerProperty(type=LoopIssuesProps)
    bpy.types.Scene.zenu_loop_issues = bpy.props.CollectionProperty(type=LoopIssue)
    bpy.types.Scene.zenu_loop_issues_active = bpy.props.IntProperty()


def unregister():
    unreg()

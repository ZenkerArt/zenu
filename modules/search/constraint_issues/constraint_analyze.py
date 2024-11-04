import json
from dataclasses import asdict
from typing import Any

import bpy
from ..constraint_issues import ConstraintData, ConstraintIssueType, IssueList, ConstraintIssueElementType
from ....utils import is_type, check_mods
from ..parent_panel import AnalyzeParentPanel


def poll():
    return is_type(bpy.context.active_object, bpy.types.Armature) and check_mods('p')


class ZENU_UL_constraints_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: bpy.types.Object, icon, active_data, active_propname):
        col = layout.column()
        if item.elem_type == ConstraintIssueElementType.HEADING:
            col.label(text=f'{item.title}', icon='BONE_DATA')
            return

        row = col.row()
        row.separator()
        row.label(text=f'{item.title}', icon=ConstraintIssueType.get_icon(item.type))

    def filter_items(self, context: bpy.types.Context,
                     data: Any,
                     property: str):
        issues = getattr(data, property)

        flt_flags = [self.bitflag_filter_item] * len(issues)
        filter = context.active_object.data.zenu_constraints_filter
        issue_filter = int(context.active_object.data.zenu_constraints_issue_filter)
        for index, issue in enumerate(issues):
            find = False

            if filter != 'ALL' and (filter not in issue.constraint_type):
                flt_flags[index] = 0
                continue

            if issue_filter != ConstraintIssueType.ALL and ((issue_filter & issue.type) == 0):
                flt_flags[index] = 0
                continue

            for i in self.filter_name.split(' '):
                find = find or (i.lower() not in issue.name.lower())

            if find:
                flt_flags[index] = 0

        return flt_flags, []


class ZENU_OT_select_bone(bpy.types.Operator):
    bl_label = 'Select Bone'
    bl_idname = 'zenu.select_bone'
    bone_name: bpy.props.StringProperty(name='Bone Name')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll()

    def execute(self, context: bpy.types.Context):
        bpy.ops.pose.select_all(action='DESELECT')
        arm: bpy.types.Armature = context.active_object.data
        bone: bpy.types.Bone = arm.bones.get(self.bone_name)
        bone.select = True
        arm.bones.active = bone
        # bone.
        return {'FINISHED'}


class ZENU_OT_analyze_constraints(bpy.types.Operator):
    bl_label = 'Analyze Constraints'
    bl_idname = 'zenu.analyze_constraints'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll()

    @staticmethod
    def target_issue(constraint: bpy.types.Constraint, target_error: str = 'Target empty',
                     subtarget_error: str = 'Subtarget empty'):
        target = constraint.target
        if hasattr(constraint, 'target') and is_type(target, bpy.types.Armature) and constraint.subtarget == '':
            return subtarget_error
        elif target is None:
            return target_error
        return None

    def find_constraint_issues(self, constraint: bpy.types.Constraint, issues: IssueList):
        name = constraint.name

        if hasattr(constraint, 'target'):
            issues.add_issue(name, self.target_issue(constraint), ConstraintIssueType.ERROR)

        if isinstance(constraint, bpy.types.KinematicConstraint):
            if constraint.pole_target is None:
                issues.add_issue(name, 'Pole target is empty', ConstraintIssueType.WARN)

            if is_type(constraint.pole_target, bpy.types.Armature) and constraint.pole_subtarget == '':
                issues.add_issue(name, 'Pole subtarget is empty', ConstraintIssueType.ERROR)

        if isinstance(constraint, bpy.types.ActionConstraint):
            if constraint.action is None:
                issues.add_issue(name, 'Action empty', ConstraintIssueType.ERROR)

        if isinstance(constraint, bpy.types.TrackToConstraint):
            up = constraint.up_axis.rsplit('_', maxsplit=1)[1]
            track = constraint.track_axis.rsplit('_', maxsplit=1)[1]
            if up == track:
                issues.add_issue(name, 'Same axis track axis and up axis', ConstraintIssueType.ERROR)

        return issues

    def execute(self, context: bpy.types.Context):
        obj = context.object
        collection: bpy.types.CollectionProperty = context.active_object.data.zenu_constraints_analyze

        collection.clear()

        for bone in obj.pose.bones:
            constraints: list[bpy.types.Constraint] = list(bone.constraints)

            if len(constraints) < 1: continue
            constraint_data_a = collection.add()
            constraint_data_a.name = bone.name
            constraint_data_a.title = bone.name
            constraint_data_a.pose_bone = bone.name
            constraint_data_a.elem_type = ConstraintIssueElementType.HEADING
            constraint_data_a.issue = '[]'

            for constraint in constraints:
                issues = self.find_constraint_issues(constraint, IssueList())
                error = ConstraintIssueType.DEFAULT
                for i in issues:
                    e = int(i.type)
                    if e > error:
                        error = e

                constraint_data = collection.add()
                constraint_data.name = f'{bone.name} {constraint.name} {constraint.type}'
                constraint_data.constraint_type = constraint.type
                constraint_data.title = constraint.name
                constraint_data.issue = json.dumps([asdict(i) for i in issues])
                constraint_data.type = error
                constraint_data.pose_bone = bone.name

                constraint_data_a.name += f' {constraint.name}'
                constraint_data_a.constraint_type += f' {constraint.type}'

                if error & constraint_data_a.type == 0:
                    constraint_data_a.type += error

        return {'FINISHED'}


class ZENU_PT_constraint_analyze(AnalyzeParentPanel):
    bl_label = 'Constraints'
    bl_context = ''

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return poll()

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        arm = context.active_object.data

        col = layout.column(align=True)
        col.operator(ZENU_OT_analyze_constraints.bl_idname, text='Update List')
        col.scale_y = 1.5
        col.row().prop(arm, 'zenu_constraints_issue_filter', expand=True)
        col.prop(arm, 'zenu_constraints_filter', text='')

        layout.template_list('ZENU_UL_constraints_list', '',
                             arm, 'zenu_constraints_analyze',
                             arm, 'zenu_constraints_analyze_active')

        try:
            selection: ConstraintData = arm.zenu_constraints_analyze[
                arm.zenu_constraints_analyze_active]
        except IndexError:
            return

        for i in json.loads(selection.issue):
            box = layout.box()
            box.label(text=i['description'], icon=ConstraintIssueType.get_icon(i['type']))


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_constraint_analyze,
    ZENU_OT_analyze_constraints,
    ZENU_UL_constraints_list,
    ZENU_OT_select_bone,
    ConstraintData
))


def on_change_constraint(scene, context):
    try:
        arm = context.render_object.data
        selection: ConstraintData = arm.zenu_constraints_analyze[arm.zenu_constraints_analyze_active]
    except IndexError:
        return

    if not bpy.ops.zenu.select_bone.poll():
        return

    bpy.ops.zenu.select_bone(bone_name=selection.bone)


def constraint_enum(scene, context):
    items = []

    for item in bpy.types.Constraint.bl_rna.properties['type'].enum_items:
        items.append((item.identifier, item.name, item.description, item.icon, item.value))

    return [
        ('ALL', 'All', ''),
        *items
    ]


def register():
    reg()
    bpy.types.Armature.zenu_constraints_issue_filter = bpy.props.EnumProperty(items=ConstraintIssueType.get_enum(),
                                                                              name='Filter')
    bpy.types.Armature.zenu_constraints_filter = bpy.props.EnumProperty(items=constraint_enum, name='Filter')
    bpy.types.Armature.zenu_constraints_analyze = bpy.props.CollectionProperty(type=ConstraintData)
    bpy.types.Armature.zenu_constraints_analyze_active = bpy.props.IntProperty(update=on_change_constraint)


def unregister():
    unreg()

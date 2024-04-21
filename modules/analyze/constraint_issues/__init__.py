from dataclasses import dataclass

import bpy


class ConstraintIssueElementType:
    DEFAULT = 'DEFAULT'
    HEADING = 'HEADING'


class ConstraintIssueType:
    ALL = 2 << 1
    DEFAULT = 2 << 2
    WARN = 2 << 3
    ERROR = 2 << 4

    @classmethod
    def get_enum(cls):
        return (
            (str(cls.ALL), 'All', '', 'MESH_PLANE', 0),
            (str(cls.DEFAULT), 'Default', '', 'SEQUENCE_COLOR_04', 1),
            (str(cls.WARN), 'Warn', '', 'SEQUENCE_COLOR_03', 2),
            (str(cls.ERROR), 'Error', '', 'SEQUENCE_COLOR_01', 3)
        )

    @classmethod
    def get_icon(cls, typ: str):
        for (etype, name, _, icon, desc) in cls.get_enum():
            if etype == str(typ):
                return icon

        return 'SEQUENCE_COLOR_04'


@dataclass
class ConstraintIssue:
    name: str
    type: str
    description: str


class ConstraintData(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Constraint Name')
    constraint_type: bpy.props.StringProperty(name='constraint_type')
    title: bpy.props.StringProperty(name='Title')
    bone: bpy.props.StringProperty(name='Bone Name')
    type: bpy.props.IntProperty(default=ConstraintIssueType.DEFAULT)
    elem_type: bpy.props.StringProperty(name='Element Type', default=ConstraintIssueElementType.DEFAULT)
    issue: bpy.props.StringProperty(name='Issue Description')


class IssueList(list[ConstraintIssue]):
    def add_issue(self, constraint_name: str, description: str, typ: int = ConstraintIssueType.DEFAULT):
        if description is None:
            return

        super().append(ConstraintIssue(
            name=constraint_name,
            description=description,
            type=str(typ)
        ))

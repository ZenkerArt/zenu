from dataclasses import dataclass, field

import bpy


def get_name(self):
    return self.obj.name


def set_name(self, text: str):
    self.obj.name = text


class AudioTrigger(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='', get=get_name, set=set_name)
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    radius: bpy.props.FloatProperty(default=.01)
    path: bpy.props.StringProperty(subtype='DIR_PATH')
    shape: bpy.props.EnumProperty(items=(
        ('Sphere', 'SPHERE', ''),
    ))


class AudioTriggerPoint(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='', get=get_name, set=set_name)
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    shape: bpy.props.EnumProperty(items=(
        ('Point', 'POINT', ''),
    ))


@dataclass
class TriggerCalcResult:
    trigger: AudioTrigger
    radius: float
    is_triggered: bool
    points: list[AudioTriggerPoint] = field(default_factory=list)

    @property
    def name(self):
        return self.trigger.name


@dataclass()
class RealtimeData:
    is_record: bool = False
    triggered: dict[str, bool] = field(default_factory=dict)

    def on_frame_update(self, triggers: list[TriggerCalcResult]):
        pass

    def on_end(self):
        pass


realtime_data = RealtimeData()

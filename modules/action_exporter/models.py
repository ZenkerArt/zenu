from dataclasses import asdict, dataclass, field
import json
import bpy


@dataclass
class ActionExportObject:
    slot: str = ''

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(
                slot=data['slot']
            )
        except Exception:
            return cls()


@dataclass
class ActionExportItem:
    objects: dict[str, ActionExportObject] = field(default_factory=dict)

    def to_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data):
        try:
            obj = json.loads(data)
            return cls(
                objects={key: ActionExportObject.from_dict(
                    value) for key, value in obj['objects'].items()}
            )
        except Exception as e:
            return cls()

    def has_object(self, name: str):
        return name in self.objects

    def get_object(self, name: str):
        return self.objects.get(name)


@dataclass
class ExportTriggerDataItem:
    frame: int = 0
    name: str = ''

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data['name'],
            frame=data['frame']
        )

    def to_dict(self):
        return asdict(self)


@dataclass
class ExportTriggerData:
    triggers: list[ExportTriggerDataItem] = field(default_factory=list)

    def add_trigger(self, frame: int, name: str):
        self.triggers.append(ExportTriggerDataItem(
            frame=frame,
            name=name
        ))

    def load_markers(self):
        data = self.triggers
        for trigger in data:

            bpy.context.scene.timeline_markers.new(
                name=trigger.name, frame=trigger.frame)

    def save_markers(self):
        self.triggers = []
        markers = bpy.context.scene.timeline_markers

        for marker in markers.values():
            self.add_trigger(
                marker.frame,
                marker.name
            )

    def to_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str):
        try:
            obj = json.loads(data)
            return cls(
                triggers=[ExportTriggerDataItem.from_dict(
                    i) for i in obj['triggers']],
            )
        except Exception as e:

            return cls()


class ActionExport(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    data: bpy.props.StringProperty()
    uuid: bpy.props.StringProperty()
    export_mesh: bpy.props.BoolProperty()
    export_textures: bpy.props.BoolProperty()
    export_path: bpy.props.StringProperty(subtype='DIR_PATH', options={
                                          'PATH_SUPPORTS_BLEND_RELATIVE'}, default='')
    export_animinfo: bpy.props.BoolProperty()
    apply_mods: bpy.props.BoolProperty()

    use_additive: bpy.props.BoolProperty()
    use_bake_only_animated: bpy.props.BoolProperty()
    action_additive: bpy.props.PointerProperty(type=bpy.types.Action)

    trigger_data: bpy.props.StringProperty()
    trigger_edit_mode: bpy.props.BoolProperty(default=False)

    def _on_select(self):
        pass

    def load_anim_info(self):
        return ActionExportItem.from_json(self.data)

    def load_triggers(self):
        return ExportTriggerData.from_json(self.trigger_data)

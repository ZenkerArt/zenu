from dataclasses import dataclass, Field, field
from typing import Any


@dataclass
class BaseItem:
    path: str = None
    text: str = None
    icon: str = None

    def _add_data(self) -> dict[str, Any]:
        return {}

    def _set_data(self, dct: dict[str, Any]):
        pass

    def to_dict(self):
        return {
            **self._add_data(),
            'class_name': type(self).__name__,
            'path': self.path,
            'text': self.text,
            'icon': self.icon
        }

    @classmethod
    def from_dict(cls, dct: dict[str]):
        self = cls(
            path=dct['path'],
            text=dct['text'],
            icon=dct['icon'],
        )
        self._set_data(dct)
        return self


@dataclass
class OperatorItem(BaseItem):
    args: dict[str, Any] = field(default_factory=dict)

    def _add_data(self) -> dict[str, Any]:
        return {
            'args': self.args
        }

    def _set_data(self, dct: dict[str, Any]):
        try:
            self.args = dct['args']
        except KeyError:
            pass


@dataclass
class PropertyItem(BaseItem):
    pass


item_classes = (OperatorItem, PropertyItem)


def create_item_from_dct(dct: dict[str, Any]) -> BaseItem | None:
    class_name = dct['class_name']

    for item in item_classes:
        if item.__name__ != class_name:
            break

        cls = item.from_dict(dct)

        return cls

    return None

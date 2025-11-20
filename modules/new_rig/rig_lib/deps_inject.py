import inspect
from typing import Callable, Type, TypeVar
T = TypeVar('T')


class DepsInject:

    _classes: list

    def __init__(self, classes: list):
        self._classes = classes

    def get_by_type(self, class_type: T) -> Type[T] | None:
        for i in self._classes:
            if isinstance(i, class_type):
                return i

    def get_deps_for_func(self, func: Callable):
        dct = {}

        for key, typ in inspect.signature(func).parameters.items():
            data = self.get_by_type(typ.annotation)

            if data is None:
                continue

            dct[key] = data

        return dct

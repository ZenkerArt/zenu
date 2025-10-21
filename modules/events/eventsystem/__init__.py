from typing import Callable
from collections import defaultdict


class EventSystem:
    _funcs: defaultdict[str, list[callable]]

    def __init__(self):
        self._funcs = defaultdict(list)

    def on(self, event: str):
        f = self._funcs

        def capture(func):
            f[event].append(func)
        return capture

    def emit(self, event: str, data = None):
        for func in self._funcs[event]:
            func(data)

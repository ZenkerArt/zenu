from ast import arg
from .rig_context import RigContext


class RigLayer:
    context: RigContext
    
    def __init__(self):
        pass

    def execute(self):
        pass


class RigLayers:
    _layers: list[RigLayer]
    _rig_context: RigContext

    def __init__(self, rig_context: RigContext):
        self._layers = []
        self._rig_context = rig_context

    def add_layer(self, layer: RigLayer):
        layer.context = self._rig_context
        self._layers.append(layer)

    def execute(self):
        for layer in self._layers:
            args = self._rig_context.deps.get_deps_for_func(layer.execute)
            layer.execute(**args)

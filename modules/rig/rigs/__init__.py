import inspect
import os
from importlib import import_module

from .rig_module import RigModule


def get_modules():
    for i in os.scandir(os.path.dirname(__file__)):
        if i.name.startswith('_') or i.name == 'rig_module.py': continue
        module = import_module(f'.{i.name.replace(".py", "")}', __package__)
        if hasattr(module, 'off'):
            continue

        for name, obj in inspect.getmembers(module):
            if name.startswith('_') or not inspect.isclass(obj) or name == RigModule.__name__: continue

            if not issubclass(obj, RigModule): continue

            yield obj()
            print(f'Load {name}')


rig_modules: tuple[RigModule] = tuple(get_modules())

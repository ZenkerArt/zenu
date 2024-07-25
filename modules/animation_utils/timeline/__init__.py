from ....utils import register_modules, unregister_modules
from . import audio_view, loop_issues, time_ranges

modules = (
    audio_view,
    loop_issues,
    time_ranges
)


def register():
    register_modules(modules)


def unregister():
    unregister_modules(modules)

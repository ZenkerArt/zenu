import bpy

from ..rig_lib import RigContext, RigLayer
from .rig_components_layer import RigComponentsLayer


class GameReadyLayer(RigLayer):
    def __init__(self):
        super().__init__()

    @classmethod
    def draw(cls, layout: bpy.types.UILayout):
        head, is_open = layout.panel('Game Ready', default_closed=False)
        head.prop(bpy.context.active_object.data, 'zenu_is_game_ready', text='Is Game ready')
        
    @classmethod
    def register(cls):
        bpy.types.Armature.zenu_is_game_ready = bpy.props.BoolProperty(default=True)

    @classmethod
    def unregister(cls):
        pass

    def execute(self, context: RigContext, components_layer: RigComponentsLayer):
        pass

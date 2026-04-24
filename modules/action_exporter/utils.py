import json
import os
from typing import TYPE_CHECKING
import bpy

if TYPE_CHECKING:
    from .action_list_export import ActionExport


def export_animinfo(item: 'ActionExport'):
    filepath = os.path.join(bpy.path.abspath(item.export_path), f'{item.name}.animinfo')
    
    with open(filepath, mode='w') as f:
        data = json.loads(item.trigger_data)
        data['fps'] = bpy.context.scene.render.fps
        data['frames'] = item.action.frame_end - item.action.frame_start
        f.write(json.dumps(data))
    
    return filepath
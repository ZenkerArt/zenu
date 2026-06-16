import bpy
from ..base_node import BaseNode


class BaseDialogNode(BaseNode):
    bl_idname = "BaseDialogNode"
    bl_label = "BaseDialogNode"
    dialog_type = ''


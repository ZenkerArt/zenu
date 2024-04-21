import bpy
from ...base_panel import BasePanel
import XInput


class GamepadSettings(bpy.types.PropertyGroup):
    use_gamepad: bpy.props.BoolProperty(default=False)

    button: bpy.props.EnumProperty(items=(
        ('rt', 'RT', ''),
        ('lt', 'LT', ''),
        ('stick_l', 'Stick L', ''),
        ('stick_r', 'Stick R', ''),
    ))
    mod: bpy.props.EnumProperty(items=(
        ('add', 'Add', ''),
        ('set', 'Set', '')
    ))
    speed: bpy.props.FloatProperty(default=.5, name='Speed', min=0, soft_max=1)


class ZENU_OT_gamepad(bpy.types.Operator):
    """Operator which runs itself from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"
    buttons = {}
    _timer = None


    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}


        state = XInput.get_state(0)
        stick_l, stick_r = XInput.get_thumb_values(state)
        lt, rt = XInput.get_trigger_values(state)
        active = context.active_object

        for i in self.buttons.get('lt', []):
            gamepad: GamepadSettings = i.zenu_gamepad

            if gamepad.mod == 'add':
                i.location.z += lt * gamepad.speed
            else:
                i.location.z = lt * gamepad.speed

        for i in self.buttons.get('rt', []):
            gamepad: GamepadSettings = i.zenu_gamepad

            if gamepad.mod == 'add':
                i.location.z += rt * gamepad.speed
            else:
                i.location.z = rt * gamepad.speed

        for i in self.buttons.get('stick_l', []):
            gamepad: GamepadSettings = i.zenu_gamepad

            if gamepad.mod == 'add':
                i.location.x += stick_l[0] * gamepad.speed
                i.location.z += stick_l[1] * gamepad.speed
            else:
                i.location.x = (stick_l[0] * gamepad.speed)
                i.location.z = -(stick_l[1] * gamepad.speed)

        for i in self.buttons.get('stick_r', []):
            gamepad: GamepadSettings = i.zenu_gamepad

            if gamepad.mod == 'add':
                i.location.x -= stick_r[0] * gamepad.speed
                i.location.z += stick_r[1] * gamepad.speed
            else:
                i.location.x = -(stick_r[0] * gamepad.speed)
                i.location.z = stick_r[1] * gamepad.speed

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.buttons.clear()

        for i in context.active_object.pose.bones:
            gamepad: GamepadSettings = i.zenu_gamepad
            if not gamepad.use_gamepad: continue

            arr = self.buttons.get(gamepad.button, [])
            self.buttons[gamepad.button] = [*arr, i]

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.033, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class ZENU_PT_gamepad(BasePanel):
    bl_label = "Gamepad"
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_pose_bone
        gamepad: GamepadSettings = obj.zenu_gamepad
        layout.operator(ZENU_OT_gamepad.bl_idname)
        lst = ['name', 'bl_rna', 'rna_type', 'use_gamepad']

        props = [i for i in dir(gamepad) if not i.startswith('_') and i not in lst]

        layout.prop(gamepad, 'use_gamepad', text='Enable', icon='RECORD_ON')

        if not gamepad.use_gamepad:
            return

        col = layout.column(align=True)
        for i in props:
            col.prop(gamepad, i)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_gamepad,
    ZENU_OT_gamepad,
    GamepadSettings
))


def register():
    reg()

    bpy.types.PoseBone.zenu_gamepad = bpy.props.PointerProperty(type=GamepadSettings)
    bpy.types.Object.zenu_gamepad = bpy.props.PointerProperty(type=GamepadSettings)


def unregister():
    unreg()

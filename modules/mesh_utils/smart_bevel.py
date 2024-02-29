from dataclasses import dataclass

import bpy
from ...utils import is_type
from .drawer import Drawer


@dataclass
class BavelSnap:
    mod: bpy.types.BevelModifier
    obj: bpy.types.Object
    show_wireframe: bool = False
    width: float = 0
    segments: int = 0
    profile: float = 0
    active: bool = False
    use_weight: bool = False


class ZENU_OT_bevel(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO_GROUPED', 'GRAB_CURSOR', 'BLOCKING'}
    bl_label = 'Bevel'
    bl_idname = 'zenu.bevel'
    _mouse_start_pos = (0, 0)
    _mouse_pos = (0, 0)
    _bevels: list[BavelSnap]
    _active_bavel: BavelSnap = None
    edit: bpy.props.BoolProperty(default=False)
    prop_count: bpy.props.IntProperty(default=2)
    prop_profile: bpy.props.BoolProperty(default=True)
    prop_copy: bpy.props.BoolProperty(default=True)
    prop_use_weight: bpy.props.BoolProperty(default=False)

    _shift: bool = False
    drawer: Drawer

    def __init__(self):
        self.drawer = Drawer()
        self._bevels = []

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_type(context.active_object, bpy.types.Mesh)

    def find_bevel(self, obj: bpy.types.Object):
        mod = None
        for mmod in obj.modifiers:
            if isinstance(mmod, bpy.types.BevelModifier):
                mod = mmod

        return mod

    def make_snap(self, bavel: bpy.types.BevelModifier) -> BavelSnap:
        return BavelSnap(
            mod=bavel,
            obj=bavel.id_data,
            show_wireframe=bavel.id_data.show_wire,
            width=bavel.width,
            segments=bavel.segments,
            profile=bavel.profile,
            active=bavel.id_data == bpy.context.active_object
        )

    def apply_snap(self, mod: bpy.types.BevelModifier, bavel_snap: BavelSnap):
        mod.segments = bavel_snap.segments
        mod.width = bavel_snap.width
        mod.profile = 1 if bavel_snap.profile >= .5 else .5
        mod.limit_method = 'WEIGHT' if bavel_snap.use_weight else 'ANGLE'
        mod.id_data.show_wire = bavel_snap.show_wireframe

    def init(self, obj: bpy.types.Object):
        if self.edit:
            mod = self.find_bevel(obj)
            if mod is None:
                return False
        else:
            mod = obj.modifiers.new(name='ZENU_Bevel', type='BEVEL')

        bevel = self.make_snap(mod)

        if bevel.active:
            self._active_bavel = bevel

        self._bevels.append(bevel)
        obj.show_wire = True
        has_subsurf = False
        sub_index = 0

        for index, m in enumerate(obj.modifiers):
            if isinstance(m, bpy.types.SubsurfModifier):
                has_subsurf = True
                sub_index = index
                break

        if has_subsurf and not self.edit:
            with bpy.context.temp_override(object=obj):
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=sub_index)

        self.apply_mod_settings(bevel)
        return True

    def apply_mod_settings(self, bevel: BavelSnap, bevel_over: BavelSnap = None):
        bevel.miter_outer = 'MITER_ARC'
        mod = bevel.mod
        bbevel = bevel_over or bevel

        if self.edit:
            mod.segments = bbevel.segments + self.prop_count
        else:
            mod.segments = self.prop_count

        mod.profile = 1 if self.prop_profile else .5
        mod.limit_method = 'WEIGHT' if self.prop_use_weight else 'ANGLE'

    def execute(self, context):
        for mod in self._bevels:
            mod_over = None
            if self.prop_copy:
                mod_over = self._active_bavel

            value = self._mouse_pos[0] - self._mouse_start_pos[0]

            result = value / 100

            if self._shift:
                result = value / 1000

            self.apply_mod_settings(mod, mod_over)

            if self.edit:
                result += mod_over.width if mod_over else mod.width

            if result < .00001:
                result = .00001

            mod.mod.width = result

        return {'FINISHED'}

    @property
    def count(self):
        return self.prop_count

    @count.setter
    def count(self, value: int):
        self.prop_count = value

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        self._shift = event.shift

        self.drawer.set_active('Shift', event.shift)

        if event.type == 'MOUSEMOVE':  # Apply
            self._mouse_pos = (event.mouse_x, event.mouse_y)
            self.execute(context)
        elif event.type == 'WHEELUPMOUSE':
            self.count += 1
            self.execute(context)
        elif event.type == 'WHEELDOWNMOUSE':
            self.count -= 1
            self.execute(context)
        elif event.type == 'W' and event.value == 'PRESS':
            self.prop_use_weight = not self.prop_use_weight
            self.drawer.set_active('W', self.prop_use_weight)
            self.execute(context)
        elif event.type == 'A' and event.value == 'PRESS':
            self.prop_copy = not self.prop_copy
            self.drawer.set_active('A', self.prop_copy)
            self.execute(context)
        elif event.type == 'S' and event.value == 'PRESS':
            self.prop_profile = not self.prop_profile
            self.drawer.set_active('S', self.prop_profile)
            self.execute(context)
        elif event.type == 'LEFTMOUSE':  # Confirm
            self.drawer.deactivate()
            for bevel_snap in self._bevels:
                bevel_snap.obj.show_wire = bevel_snap.show_wireframe

            if self.edit:
                self.report({'INFO'}, 'Bavel Modified')
            else:
                self.report({'INFO'}, 'Bavel Added')
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            for bevel_snap in self._bevels:
                if self.edit:
                    self.apply_snap(bevel_snap.mod, bevel_snap)
                else:
                    bevel_snap.obj.modifiers.remove(bevel_snap.mod)
            self.drawer.deactivate()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self._mouse_start_pos = (event.mouse_x, event.mouse_y)
        self._mouse_pos = (event.mouse_x, event.mouse_y)

        has_bavel = False

        for obj in context.selected_objects:
            if self.init(obj):
                has_bavel = True

        if not has_bavel and self.edit:
            self.report({'WARNING'}, 'Not Found Bevel')
            return {'CANCELLED'}

        if has_bavel and self.edit:
            self.prop_count = 0

        self.execute(context)

        self.drawer = Drawer()
        self.drawer.activate()

        self.drawer.add_shortcut('Wheel Down/Up', 'Segment Count')
        self.drawer.add_shortcut('Shift', 'Slow Mode')
        if self.edit:
            self.drawer.add_shortcut('A', 'Copy From Active')
        self.drawer.add_shortcut('W', 'Bavel Weight')
        self.drawer.add_shortcut('S', 'Profile = 1')

        self.drawer.set_active('S', self.prop_profile)
        self.drawer.set_active('A', self.prop_copy)
        self.drawer.set_active('W', self.prop_use_weight)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

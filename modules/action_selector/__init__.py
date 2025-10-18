from dataclasses import dataclass, field
from gettext import find
from ...base_panel import BasePanel
import bpy


def add_empty(name: str):
    empty = bpy.data.objects.get(name)

    if empty:
        return empty

    empty = bpy.data.objects.new(name, None)
    bpy.context.view_layer.layer_collection.collection.objects.link(empty)

    return empty


class AC_Action(bpy.types.PropertyGroup):
    name: str
    action: bpy.props.PointerProperty(type=bpy.types.Action)
    start: bpy.props.IntProperty()
    end: bpy.props.IntProperty()
    isolate: bpy.props.BoolProperty()


class ZENU_UL_action_selector(bpy.types.UIList):
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data, item: AC_Action, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False)
        # layout.prop(item, 'action', text='', emboss=False)


class ZENU_OT_clear_nla(bpy.types.Operator):
    bl_label = 'Clear NLA'
    bl_idname = 'zenu.clear_nla'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        for obj in bpy.data.objects:
            if obj.animation_data is None:
                continue

            tracks = obj.animation_data.nla_tracks

            for track in tracks:
                if len(track.strips) <= 0:
                    tracks.remove(track)

            if len(tracks) <= 0 and obj.animation_data.action is None:
                obj.animation_data_clear()
                continue

        return {'FINISHED'}


class ZENU_OT_action_selector_operations(bpy.types.Operator):
    bl_label = 'Action Selector Operations'
    bl_idname = 'zenu.action_selector_operations'
    bl_options = {'UNDO'}

    action: bpy.props.EnumProperty(items=(
        ('ADD', 'Add', ''),
        ('REMOVE', 'Remove', ''),
        ('UP', 'Up', ''),
        ('DOWN', 'Down', ''),
    ))

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        layers: bpy.types.CollectionProperty = scene.zenu_action_selector
        layers_active: int = scene.zenu_action_selector_active

        if self.action == 'ADD':
            item: AC_Action = layers.add()
            # item.obj = context.active_object
            item.name = 'Name'
        elif self.action == 'REMOVE':
            layers.remove(layers_active)
        elif self.action == 'UP':
            layers.move(layers_active, layers_active - 1)
            scene.zenu_action_selector_active = layers_active - 1
        elif self.action == 'DOWN':
            layers.move(layers_active, layers_active + 1)
            scene.zenu_action_selector_active = layers_active + 1
        return {'FINISHED'}


@dataclass
class ActionSearchResult:
    obj: bpy.types.Object
    tracks: set[bpy.types.NlaTrack] = field(default_factory=set)
    strips: list[bpy.types.NlaStrip] = field(default_factory=list)

    def __hash__(self):
        return hash(self.obj)


def find_all_object_with_action_name(name: str) -> set[ActionSearchResult]:
    finded = set()

    for obj in bpy.data.objects:
        data = ActionSearchResult(
            obj=obj
        )

        if obj.animation_data is None or len(obj.animation_data.nla_tracks) <= 0:
            continue

        for track in obj.animation_data.nla_tracks:
            for strip in track.strips:
                if strip.action.name != name:
                    continue
                data.tracks.add(track)
                data.strips.append(strip)
                finded.add(data)

    return finded


class ZENU_OT_copy_nla_strip_settings(bpy.types.Operator):
    bl_label = 'Copy NLA Strip Settings'
    bl_idname = 'zenu.copy_nla_strip_settings'
    bl_options = {'UNDO'}

    action_name: bpy.props.StringProperty()

    def copy(self, strip: bpy.types.NlaStrip, active_strip: bpy.types.NlaStrip, name: str):
        for active_curve in active_strip.fcurves:
            if active_curve.data_path != name:
                continue

            for copy_curve in strip.fcurves:
                if copy_curve.data_path != name:
                    continue

                copy_curve.keyframe_points.clear()
                copy_curve.keyframe_points.add(len(active_curve.keyframe_points))

                for index, key_active in enumerate(active_curve.keyframe_points):
                    k = copy_curve.keyframe_points[index]
                    k.co = key_active.co

                    k.handle_left_type = key_active.handle_left_type
                    k.handle_right_type = key_active.handle_right_type

                    k.handle_left = key_active.handle_left
                    k.handle_right = key_active.handle_right

                    k.easing = key_active.easing
                    k.interpolation = key_active.interpolation

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        item: AC_Action = None
        scene = context.scene

        for active_curve in scene.zenu_action_selector:
            active_curve: AC_Action
            if active_curve.action and active_curve.action.name == self.action_name:
                item = active_curve
                break

        if item is None:
            return {'FINISHED'}

        result = find_all_object_with_action_name(item.action.name)
        active_strip: bpy.types.NlaStrip = None
        for obj in context.selected_objects:
            if obj.animation_data is None:
                continue

            for track in obj.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.active:
                        active_strip = strip

        if active_strip is None:
            return {'CANCELLED'}

        for action in result:
            try:
                action.strips.remove(active_strip)
            except ValueError:
                pass

            for strip in action.strips:
                strip.use_sync_length = active_strip.use_sync_length
                strip.use_animated_time = active_strip.use_animated_time
                strip.use_animated_influence = active_strip.use_animated_influence
                strip.repeat = active_strip.repeat
                strip.scale = active_strip.scale

                self.copy(strip, active_strip, 'strip_time')
                self.copy(strip, active_strip, 'influence')

        return {'FINISHED'}


class ZENU_OT_action_selector_item_operations(bpy.types.Operator):
    bl_label = 'Action Selector Item Operations'
    bl_idname = 'zenu.action_selector_item_operations'
    bl_options = {'UNDO'}

    action_name: bpy.props.StringProperty()
    action: bpy.props.EnumProperty(items=(
        ('SELECT', 'Select', ''),
        ('RENAME_TO_ACTION_NAME', 'Rename To Action Name', ''),
        ('ISOLATE', 'Isolate With Action', ''),
    ))

    active_action: AC_Action = None

    def unhide(self, result: set[ActionSearchResult]):
        empty = add_empty('Select')
        bpy.context.view_layer.objects.active = empty
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects.remove(empty)

        for find in result:
            try:
                find.obj.hide_viewport = False
                find.obj.hide_set(False)
                find.obj.select_set(True)
            except RuntimeError:
                for i in find.obj.users_collection:
                    i: bpy.types.Collection
                    bpy.context.view_layer.layer_collection.children[i.name].exclude = False

                find.obj.hide_viewport = False
                find.obj.hide_set(False)
                find.obj.select_set(True)

    def select(self, result: set[ActionSearchResult]):

        self.unhide(result)

        for find in result:
            for track in find.obj.animation_data.nla_tracks:
                for strip in track.strips:
                    strip.select = False

            for strip in find.strips:
                strip.select = True

        if result:
            bpy.context.view_layer.objects.active = result.pop().obj

    def isolate(self, result: set[ActionSearchResult]):
        self.unhide(result)

        for r in result:
            strips: list[bpy.types.NlaStrip] = []

            for track in r.obj.animation_data.nla_tracks:
                for strip in track.strips:
                    strips.append(strip)

            if r.obj.zenu_is_isolate:
                bpy.context.scene.use_preview_range = False
                r.obj.zenu_is_isolate = False
                r.obj.animation_data.action = r.obj['zenu_isolate_changes']['action']
                for strip in strips:
                    val = r.obj['zenu_isolate_changes']['changes'].get(
                        strip.name)

                    if val is None:
                        continue

                    strip.mute = val
                continue

            changes = {}
            for strip in strips:
                if not strip.mute:
                    changes[strip.name] = False
                    strip.mute = True

            r.obj['zenu_isolate_changes'] = {
                'changes': changes,
                'action': r.obj.animation_data.action
            }
            r.obj.animation_data.action = self.active_action.action
            r.obj.zenu_is_isolate = True
            
            if self.active_action.start == self.active_action.end:
                continue
            
            bpy.context.scene.frame_preview_end = self.active_action.end
            bpy.context.scene.frame_preview_start = self.active_action.start
            bpy.context.scene.use_preview_range = True

    def execute(self, context: bpy.types.Context):
        item: AC_Action = None
        scene = context.scene

        for i in scene.zenu_action_selector:
            i: AC_Action

            if i.action and i.action.name == self.action_name:
                item = i
                break

        if item is None:
            return {'FINISHED'}

        self.active_action = item

        result = find_all_object_with_action_name(item.action.name)
        

        if self.action == 'SELECT':
            self.select(result)
        elif self.action == 'ISOLATE':
            self.isolate(result)
        elif self.action == 'RENAME_TO_ACTION_NAME':
            for find in result:
                for strip in find.strips:
                    strip.name = strip.action.name

        return {'FINISHED'}


class ZENU_PT_action_selector(BasePanel):
    bl_label = "Action Selector"
    bl_context = ''
    action_name: str = ''

    def draw_set_op(self, layout: bpy.types.UILayout, name: str, icon: str, action: str, active: bool = False):
        op = layout.operator(
            ZENU_OT_action_selector_item_operations.bl_idname, text=name, icon=icon, depress=active)
        op.action_name = self.action_name
        op.action = action

    def draw_settings(self, layout: bpy.types.UILayout):
        context = bpy.context
        scene = context.scene

        actions: bpy.types.CollectionProperty = scene.zenu_action_selector
        action_index: int = scene.zenu_action_selector_active

        try:
            action_active: AC_Action = actions[action_index]
        except IndexError:
            return

        col = layout.column(align=True)

        col.prop(action_active, 'action', text='')

        if action_active.action is None:
            return

        col.prop(action_active.action, 'name', text='')
        row = col.row(align=True)
        row.prop(action_active, 'start', text='')
        row.prop(action_active, 'end', text='')
        
        main_col = layout.column(align=True)

        row = main_col.row(align=True)
        row.scale_y = 2
        self.action_name = action_active.action.name

        self.draw_set_op(row, name='Select',
                         icon='RESTRICT_SELECT_OFF', action='SELECT')
        self.draw_set_op(row, name='Rename', icon='GREASEPENCIL',
                         action='RENAME_TO_ACTION_NAME')

        is_isolate = False

        try:
            obj = context.selected_objects[0]
            is_isolate = obj.zenu_is_isolate
        except IndexError:
            pass

        self.draw_set_op(row, name='Isolate',
                         icon='OBJECT_HIDDEN', action='ISOLATE', active=is_isolate)

        op = main_col.operator(ZENU_OT_copy_nla_strip_settings.bl_idname)
        op.action_name = action_active.action.name

    def draw_op(self, layout: bpy.types.UILayout, action: str, icon: str):
        op = layout.operator(
            ZENU_OT_action_selector_operations.bl_idname,
            icon=icon,
            text=''
        )
        op.action = action

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list('ZENU_UL_action_selector', '',
                          scene, 'zenu_action_selector',
                          scene, 'zenu_action_selector_active')

        col = row.column(align=True)
        self.draw_op(layout=col, action='ADD', icon='ADD')
        self.draw_op(layout=col, action='REMOVE', icon='REMOVE')

        col = row.column(align=True)
        self.draw_op(layout=col, action='UP', icon='TRIA_UP')
        self.draw_op(layout=col, action='DOWN', icon='TRIA_DOWN')

        self.draw_settings(layout)

        layout.operator(ZENU_OT_clear_nla.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_action_selector,
    ZENU_OT_action_selector_operations,
    ZENU_OT_action_selector_item_operations,
    ZENU_OT_copy_nla_strip_settings,
    ZENU_OT_clear_nla,
    AC_Action,
    ZENU_UL_action_selector
))


def register():
    reg()
    bpy.types.Object.zenu_is_isolate = bpy.props.BoolProperty(
        default=False, options={'ANIMATABLE'})
    bpy.types.Scene.zenu_action_selector = bpy.props.CollectionProperty(
        type=AC_Action)
    bpy.types.Scene.zenu_action_selector_active = bpy.props.IntProperty()


def unregister():
    unreg()

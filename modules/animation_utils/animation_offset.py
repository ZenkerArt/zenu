import bpy
from ...base_panel import BasePanel


class OffsetType:
    ROTATION: str = 'ROTATION'
    LOCATION: str = 'LOCATION'
    SCALE: str = 'SCALE'
    LOCATION_ROTATION: str = ROTATION + LOCATION
    LOCATION_ROTATION_SCALE: str = ROTATION + LOCATION + SCALE

    @classmethod
    def to_enum(cls):
        return (
            (cls.LOCATION, 'Location', ''),
            (cls.ROTATION, 'Rotation', ''),
            (cls.SCALE, 'Scale', ''),
            (cls.LOCATION_ROTATION, 'Location, Rotation', ''),
            (cls.LOCATION_ROTATION_SCALE, 'Location, Rotation, Scale', ''),
        )


class AnimationOffsetProps(bpy.types.PropertyGroup):
    offset: bpy.props.IntProperty(name='Offset')
    offset_step: bpy.props.IntProperty(name='Offset Step')
    offset_type: bpy.props.EnumProperty(items=OffsetType.to_enum())


class ZENU_PT_animation_utils_ge(BasePanel):
    bl_label = 'Animation Utils'
    bl_space_type = 'GRAPH_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


class ZENU_PT_animation_utils_de(BasePanel):
    bl_label = 'Animation Utils'
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


class ZENU_OT_animation_offsets(bpy.types.Operator):
    bl_label = 'Animation Offsets'
    bl_idname = 'zenu.animation_offsets'
    bl_options = {'REGISTER', 'UNDO'}
    direction: bpy.props.BoolProperty(default=True)

    def execute(self, context: bpy.types.Context):
        action: bpy.types.Action = context.active_object.animation_data.action
        store: AnimationOffsetProps = context.scene.zenu_animation_offset

        selected = [pose.name for pose in context.selected_pose_bones]

        for i in action.fcurves:
            try:
                prop = i.data_path.rsplit('.', maxsplit=1)[1]
            except IndexError:
                continue

            go = False
            for name in selected:
                if f'"{name}"' in i.data_path:
                    go = True
                    break

            if not go:
                continue

            is_rotation = prop == 'rotation_quaternion' or prop == 'rotation_euler'
            is_location = prop == 'location'
            is_scale = prop == 'scale'
            offset = store.offset
            result = False

            if store.offset_type == OffsetType.LOCATION:
                result = is_location

            if store.offset_type == OffsetType.ROTATION:
                result = is_rotation

            if store.offset_type == OffsetType.SCALE:
                result = is_scale

            if store.offset_type == OffsetType.LOCATION_ROTATION:
                result = is_location or is_scale

            if not self.direction:
                offset = -offset

            if result:
                for key in i.keyframe_points:
                    key.co_ui.x += offset
        return {'FINISHED'}


def draw(self, context: bpy.types.Context):
    store: AnimationOffsetProps = context.scene.zenu_animation_offset

    layout = self.layout
    layout.prop(store, 'offset_type', text='')

    col = layout.column_flow(align=True)

    col.prop(store, 'offset', text='')
    row = col.row(align=True)
    row.scale_x = 100
    op = row.operator(ZENU_OT_animation_offsets.bl_idname, text='', icon='ADD')
    op.direction = True
    op = row.operator(ZENU_OT_animation_offsets.bl_idname, text='', icon='REMOVE')
    op.direction = False


classes = (
    ZENU_OT_animation_offsets,
    ZENU_PT_animation_utils_ge,
    ZENU_PT_animation_utils_de,
    AnimationOffsetProps,
)

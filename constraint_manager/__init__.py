import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from ..base_panel import BasePanel
from ..utils import check_mods

types = (
    'CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER', 'COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS',
    'LIMIT_DISTANCE', 'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME', 'TRANSFORM',
    'TRANSFORM_CACHE',
    'CLAMP_TO', 'DAMPED_TRACK', 'IK', 'LOCKED_TRACK', 'SPLINE_IK', 'STRETCH_TO', 'TRACK_TO', 'ACTION', 'ARMATURE',
    'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP'
)


class ConstraintGizmo:
    shader = None
    shader_handler = None

    def __init__(self):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

    @staticmethod
    def update():
        for region in bpy.context.area.regions:
            if region.type == 'WINDOW':
                region.tag_redraw()

    def draw(self):
        coords = [(1, 1, 1), (-2, 0, 0), (-2, -1, 3), (0, 1, 1)]
        batch = batch_for_shader(self.shader, 'LINES', {'pos': coords})
        self.shader.uniform_float('color', (1, 1, 0, 1))
        batch.draw(self.shader)

    @property
    def is_enable(self):
        return self.shader_handler is None

    def enable_gizmo(self):
        if self.shader_handler is not None:
            return

        self.shader_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')
        self.update()

    def disable_gizmo(self):
        if self.shader_handler is None:
            return

        bpy.types.SpaceView3D.draw_handler_remove(self.shader_handler, 'WINDOW')
        self.shader_handler = None
        self.update()

    def toggle(self):
        if self.shader_handler is None:
            self.enable_gizmo()
        else:
            self.disable_gizmo()


gizmo = ConstraintGizmo()


class ZENU_PT_constraint_manager(BasePanel):
    bl_label = 'Constraint Manager'
    bl_context = ''

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return check_mods('ope')

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ZENU_OT_create_constraint.bl_idname, text='Limit loc').type = 'LIMIT_LOCATION'
        layout.operator(ZENU_OT_enable_constraint_view.bl_idname, text='Show Gizmo')


class ZENU_OT_enable_constraint_view(bpy.types.Operator):
    bl_label = 'Create Constraint'
    bl_idname = 'zenu.enable_constraint_view'

    # bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        gizmo.toggle()
        return {'FINISHED'}


class ZENU_OT_create_constraint(bpy.types.Operator):
    bl_label = 'Create Constraint'
    bl_idname = 'zenu.create_constraint'
    bl_options = {'UNDO'}
    type: bpy.props.StringProperty(name='Constraint Type')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object or context.active_bone

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if context.object.mode == 'POSE':
            obj = context.active_pose_bone
        obj.constraints.new(self.type)
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_constraint_manager,
    ZENU_OT_create_constraint,
    ZENU_OT_enable_constraint_view
))


def register():
    reg()


def unregister():
    gizmo.disable_gizmo()
    unreg()

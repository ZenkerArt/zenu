import bpy
from mathutils import Vector
from ...base_panel import BasePanel
from ...utils import update_window

resolutions_2d = [
    (1280, 720, 'HD'),
    (1920, 1080, 'Full HD'),
    (2560, 1440, '2K'),
    (3840, 2160, '4K'),
]

resolutions_vr = [
    (1024, 1024, '2K'),
    (2048, 2048, '4K'),
    (3056, 3056, '6K'),
    (4096, 4096, '8K'),
]

samples = [8, 32, 128, 256]


def setup_vr(context: bpy.types.Context, camera_obj: bpy.types.Object):
    scene = context.scene

    scene.render.image_settings.views_format = 'STEREO_3D'
    scene.render.image_settings.stereo_3d_format.display_mode = 'SIDEBYSIDE'
    scene.render.use_multiview = True

    if camera_obj is None:
        return {'FINISHED'}

    camera: bpy.types.Camera = camera_obj.data
    camera.type = 'PANO'
    camera.panorama_type = 'EQUIRECTANGULAR'
    camera.stereo.convergence_mode = 'PARALLEL'

    camera.longitude_min = -1.5708
    camera.longitude_max = 1.5708
    camera.stereo.use_spherical_stereo = True
    camera.stereo.pivot = 'CENTER'


def setup_2d(context: bpy.types.Context, camera_obj: bpy.types.Object):
    scene = context.scene
    scene.render.use_multiview = False

    if camera_obj is None:
        return {'FINISHED'}

    camera: bpy.types.Camera = camera_obj.data
    camera.panorama_type = 'EQUIRECTANGULAR'


def camera_poll(self, obj):
    return isinstance(obj.data, bpy.types.Camera)


class RenderSetupSettings(bpy.types.PropertyGroup):
    camera_2d: bpy.props.PointerProperty(type=bpy.types.Object, name='Camera 2D', poll=camera_poll)
    camera_vr: bpy.props.PointerProperty(type=bpy.types.Object, name='Camera VR', poll=camera_poll)


class ZENU_OT_set_render_settings(bpy.types.Operator):
    bl_label = 'Set Render Settings'
    bl_idname = 'zenu.set_render_settings'

    samples: bpy.props.IntProperty(name='Samples', default=-1)
    use_render_region: bpy.props.BoolProperty(name='Use Render Region', default=False)
    use_simplify: bpy.props.BoolProperty(name='Use Simplify', default=False)
    resolution: bpy.props.IntVectorProperty(name='Resolution', default=(-1, -1, -1))
    render_type: bpy.props.EnumProperty(items=[
        ('vr', 'Setup VR', ''),
        ('2d', 'Setup 2D', '')
    ])

    def execute(self, context: bpy.types.Context):
        return {'FINISHED'}


class ZENU_OT_setup_render(bpy.types.Operator):
    bl_label = 'Set Resolution'
    bl_idname = 'zenu.set_resolution'
    width: bpy.props.IntProperty(name='Width')
    height: bpy.props.IntProperty(name='Height')
    render_type: bpy.props.EnumProperty(items=[
        ('vr', 'Setup VR', ''),
        ('2d', 'Setup 2D', '')
    ])

    def execute(self, context: bpy.types.Context):
        update_window()
        scene = context.scene

        context.scene.render.resolution_x = self.width
        context.scene.render.resolution_y = self.height
        settings: RenderSetupSettings = scene.zenu_render_setup

        if self.render_type == 'vr':
            setup_vr(context, settings.camera_vr)
            scene.camera = settings.camera_vr

        if self.render_type == '2d':
            setup_2d(context, settings.camera_2d)
            scene.camera = settings.camera_2d
        return {'FINISHED'}


class ZENU_OT_set_sample(bpy.types.Operator):
    bl_label = 'Set Sample'
    bl_idname = 'zenu.set_samples'
    samples: bpy.props.IntProperty()

    def execute(self, context: bpy.types.Context):
        context.scene.cycles.samples = self.samples
        return {'FINISHED'}


class ZENU_PT_render_settings(BasePanel):
    bl_label = 'Render Settings'
    bl_context = ''

    def draw_camera_settings(self, layout: bpy.types.UILayout, obj: bpy.types.Object):
        camera: bpy.types.Camera = obj.data

        header, body = layout.panel('camera_settings', default_closed=True)
        header: bpy.types.UILayout
        body: bpy.types.UILayout
        header.label(text='Camera Settings')

        if body is None:
            return

        col = body.column(align=True)
        col.prop(camera, 'lens_unit', text='')
        if camera.lens_unit == 'FOV':
            col.prop(camera, 'angle')
        else:
            col.prop(camera, 'lens')

        col = body.column(align=True)
        col.prop(camera.dof, 'focus_distance', text='')
        col.prop(camera.dof, 'aperture_fstop', text='')

    def render_setups(self, layout: bpy.types.UILayout):
        context = bpy.context
        rd = bpy.context.scene.render
        resolution_hash = rd.resolution_x + rd.resolution_y
        scene = context.scene
        settings: RenderSetupSettings = scene.zenu_render_setup

        layout.label(text='2D Setup')
        col = layout.column_flow(align=True)
        col.prop(settings, 'camera_2d', text='')
        row = col.row(align=True)
        for width, height, type in resolutions_2d:
            cur_hash = width + height
            op = row.operator(ZENU_OT_setup_render.bl_idname, text=type, depress=cur_hash == resolution_hash)
            op.width = width
            op.height = height
            op.render_type = '2d'

        layout.label(text='VR Setup')
        col = layout.column_flow(align=True)
        col.prop(settings, 'camera_vr', text='')

        row = col.row(align=True)
        if settings.camera_vr:
            col.prop(settings.camera_vr.data.stereo, 'interocular_distance')

        for width, height, type in resolutions_vr:
            cur_hash = width + height
            op = row.operator(ZENU_OT_setup_render.bl_idname, text=type, depress=cur_hash == resolution_hash)
            op.width = width
            op.height = height
            op.render_type = 'vr'

    def render_settings(self, layout: bpy.types.UILayout):
        context = bpy.context
        scene = context.scene
        layout.label(text='Settings')
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(scene.render.image_settings, 'file_format')
        col.prop(scene.render, 'filepath')
        col.prop(scene, 'frame_step')

        col.prop(scene.render, 'film_transparent')
        if scene.render.film_transparent:
            col.prop(scene.cycles, 'film_transparent_glass')

        col.prop(scene.render, 'use_border')

        col.prop(scene.render, 'use_simplify')
        if scene.render.use_simplify:
            box = col.box()

            c = box.column(align=True)
            c.prop(scene.render, 'simplify_subdivision_render', text='Render Sub')
            c.prop(scene.cycles, 'texture_limit_render', text='Render Tex')

            c = box.column(align=True)
            c.prop(scene.render, 'simplify_subdivision', text='Viewport Sub')
            c.prop(scene.cycles, 'texture_limit', text='View Tex')

        col.prop(scene.cycles, 'use_auto_tile')
        if scene.cycles.use_auto_tile:
            col.prop(scene.cycles, 'tile_size')
            
        col.prop(scene.render, 'use_persistent_data')

        row = layout.row(align=True)
        for i in samples:
            op = row.operator(ZENU_OT_set_sample.bl_idname, text=f'{i}', depress=context.scene.cycles.samples == i)
            op.samples = i

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        data: RenderSetupSettings = context.scene.zenu_render_setup

        self.render_setups(layout)
        self.render_settings(layout)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_setup_render,
    ZENU_OT_set_sample,
    ZENU_PT_render_settings,
    RenderSetupSettings
))


def register():
    reg()
    bpy.types.Scene.zenu_render_setup = bpy.props.PointerProperty(type=RenderSetupSettings)


def unregister():
    unreg()

import bpy
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


def get_render_settings():
    settings: RenderSetupSettings = bpy.context.scene.zenu_render_setup

    render_settings: RenderSettings

    if settings.render_type == '2D':
        render_settings = bpy.context.scene.zenu_render_2d
    else:
        render_settings = bpy.context.scene.zenu_render_vr

    return render_settings


def setup():
    render_settings = get_render_settings()
    context = bpy.context

    context.scene.render.resolution_x = render_settings.width
    context.scene.render.resolution_y = render_settings.height


def setup_vr(context: bpy.types.Context, camera_obj: bpy.types.Object):
    setup()
    scene = context.scene

    scene.render.image_settings.views_format = 'STEREO_3D'
    scene.render.image_settings.stereo_3d_format.display_mode = 'SIDEBYSIDE'
    scene.render.use_multiview = True

    if camera_obj is None:
        return {'FINISHED'}

    camera: bpy.types.Camera = camera_obj.data
    camera.type = 'PANO'
    camera.panorama_type = 'EQUIRECTANGULAR'
    camera.stereo.convergence_mode = 'TOE'

    camera.longitude_min = -1.5708
    camera.longitude_max = 1.5708
    camera.stereo.use_spherical_stereo = False
    camera.stereo.pivot = 'CENTER'
    camera.stereo.convergence_distance = 3


def setup_2d(context: bpy.types.Context, camera_obj: bpy.types.Object):
    setup()
    scene = context.scene
    scene.render.use_multiview = False

    if camera_obj is None:
        return {'FINISHED'}

    camera: bpy.types.Camera = camera_obj.data
    camera.panorama_type = 'EQUIRECTANGULAR'


def camera_poll(self, obj):
    return isinstance(obj.data, bpy.types.Camera)


def on_tab_change(self, context: bpy.types.Context):
    scene = context.scene
    settings: RenderSetupSettings = scene.zenu_render_setup

    match self.render_type:
        case '2D':
            setup_2d(context, settings.camera_vr)
            scene.camera = settings.camera_2d
        case 'VR':
            setup_vr(context, settings.camera_vr)
            scene.camera = settings.camera_vr


class RenderSetupSettings(bpy.types.PropertyGroup):
    camera_2d: bpy.props.PointerProperty(
        type=bpy.types.Object, name='Camera 2D', poll=camera_poll)
    camera_vr: bpy.props.PointerProperty(
        type=bpy.types.Object, name='Camera VR', poll=camera_poll)

    render_type: bpy.props.EnumProperty(items=(
        ('2D', '2D', '2D Setup'),
        ('VR', 'VR', 'VR Setup')
    ), update=on_tab_change)

    frame_end: bpy.props.IntProperty()
    frame_start: bpy.props.IntProperty()


class RenderSettings(bpy.types.PropertyGroup):
    width: bpy.props.IntProperty()
    height: bpy.props.IntProperty()
    path: bpy.props.StringProperty()


class ZENU_OT_set_final_settings(bpy.types.Operator):
    bl_label = 'Set Final'
    bl_idname = 'zenu.set_final_settings'

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        render = scene.render
        settings: RenderSetupSettings = bpy.context.scene.zenu_render_setup
        render_settings = get_render_settings()

        render.use_simplify = False
        render.use_persistent_data = True
        scene.frame_step = 2
        render.use_border = False
        scene.cycles.samples = 128
        render.image_settings.file_format = 'PNG'
        render.image_settings.compression = 15

        render.filepath = render_settings.path

        match settings.render_type:
            case '2D':
                res = resolutions_2d[len(resolutions_2d) - 1]

                render_settings.width = res[0]
                render_settings.height = res[1]
                setup_2d(context, settings.camera_vr)
                scene.camera = settings.camera_2d
            case 'VR':
                res = resolutions_vr[len(resolutions_vr) - 1]

                render_settings.width = res[0]
                render_settings.height = res[1]

                setup_vr(context, settings.camera_vr)
                scene.camera = settings.camera_vr

        update_window()
        return {'FINISHED'}


class ZENU_OT_set_preview_settings(bpy.types.Operator):
    bl_label = 'Set Preview'
    bl_idname = 'zenu.set_preview_settings'

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        render = scene.render
        settings: RenderSetupSettings = bpy.context.scene.zenu_render_setup
        render_settings = get_render_settings()

        render.use_simplify = True
        render.use_persistent_data = True
        scene.frame_step = 2
        # render.use_border = False
        scene.cycles.samples = 8
        render.image_settings.file_format = 'FFMPEG'
        render_settings.path = render.filepath
        render.filepath = '//Renders/'

        render.ffmpeg.format = 'MPEG4'
        render.ffmpeg.codec = 'H264'
        render.ffmpeg.constant_rate_factor = 'MEDIUM'
        render.ffmpeg.ffmpeg_preset = 'GOOD'
        render.ffmpeg.audio_codec = 'AAC'

        render.simplify_subdivision = 0
        scene.cycles.texture_limit = '1024'

        match settings.render_type:
            case '2D':
                res = resolutions_2d[0]

                render_settings.width = res[0]
                render_settings.height = res[1]
                setup_2d(context, settings.camera_vr)
                scene.camera = settings.camera_2d
            case 'VR':
                res = resolutions_vr[1]

                render_settings.width = res[0]
                render_settings.height = res[1]

                setup_vr(context, settings.camera_vr)
                scene.camera = settings.camera_vr

        update_window()
        return {'FINISHED'}


class ZENU_OT_setup_render(bpy.types.Operator):
    bl_label = 'Set Resolution'
    bl_idname = 'zenu.set_resolution'
    width: bpy.props.IntProperty(name='Width')
    height: bpy.props.IntProperty(name='Height')
    render_type: bpy.props.EnumProperty(items=[
        ('VR', 'Setup VR', ''),
        ('2D', 'Setup 2D', '')
    ])

    def execute(self, context: bpy.types.Context):
        render_settings = get_render_settings()
        update_window()
        scene = context.scene

        render_settings.width = self.width
        render_settings.height = self.height
        settings: RenderSetupSettings = scene.zenu_render_setup

        if self.render_type == 'VR':
            setup_vr(context, settings.camera_vr)
            scene.camera = settings.camera_vr

        if self.render_type == '2D':
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


class ZENU_OT_save_time(bpy.types.Operator):
    bl_label = 'Save Time'
    bl_idname = 'zenu.save_time'

    load: bpy.props.BoolProperty()

    def execute(self, context: bpy.types.Context):
        settings: RenderSetupSettings = context.scene.zenu_render_setup

        if self.load:
            context.scene.frame_end = settings.frame_end
            context.scene.frame_start = settings.frame_start
        else:
            settings.frame_end = context.scene.frame_end
            settings.frame_start = context.scene.frame_start
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

    def draw_resolutions(self, layout: bpy.types.UILayout, resolutions):
        settings = bpy.context.scene.zenu_render_setup
        rd = bpy.context.scene.render
        resolution_hash = rd.resolution_x + rd.resolution_y

        row = layout.row(align=True)
        for width, height, type in resolutions:
            cur_hash = width + height
            op = row.operator(ZENU_OT_setup_render.bl_idname,
                              text=type, depress=cur_hash == resolution_hash)
            op.width = width
            op.height = height
            op.render_type = settings.render_type

    def setup_2d(self, layout: bpy.types.UILayout):
        context = bpy.context
        scene = context.scene
        settings: RenderSetupSettings = scene.zenu_render_setup

        # layout.label(text='2D Setup')
        col = layout.column_flow(align=True)
        col.prop(settings, 'camera_2d', text='')
        self.draw_resolutions(col, resolutions_2d)

    def setup_vr(self, layout: bpy.types.UILayout):
        context = bpy.context
        scene = context.scene
        settings: RenderSetupSettings = scene.zenu_render_setup

        # layout.label(text='VR Setup')
        col = layout.column_flow(align=True)
        col.prop(settings, 'camera_vr', text='')

        if settings.camera_vr:
            col.prop(settings.camera_vr.data.stereo, 'interocular_distance')

        self.draw_resolutions(col, resolutions_vr)

    def render_setups(self, layout: bpy.types.UILayout):
        context = bpy.context
        scene = context.scene
        settings: RenderSetupSettings = scene.zenu_render_setup

        match settings.render_type:
            case 'VR': self.setup_vr(layout)
            case '2D': self.setup_2d(layout)

    def render_settings(self, layout: bpy.types.UILayout):
        context = bpy.context
        scene = context.scene
        layout.label(text='Settings')
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        row = col.row(align=True)
        for i in samples:
            op = row.operator(ZENU_OT_set_sample.bl_idname,
                              text=f'{i}', depress=context.scene.cycles.samples == i)
            op.samples = i
        col.prop(scene.cycles, 'samples', text='')

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

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        data: RenderSetupSettings = context.scene.zenu_render_setup

        layout.prop(data, 'render_type', expand=True)

        self.render_setups(layout)
        self.render_settings(layout)

        row = layout.row(align=True)
        row.scale_y = 2
        row.scale_y = 2
        row.operator(ZENU_OT_set_final_settings.bl_idname,
                     icon='RESTRICT_RENDER_OFF')
        row.operator(ZENU_OT_set_preview_settings.bl_idname,
                     icon='RESTRICT_VIEW_OFF')

        layout.label(text='Timeline')

        col = layout.column()
        col.scale_y = 1.2  # FILE_TICK

        row = col.row(align=True)
        # row.prop(data, 'frame_start', text='')
        # row.prop(data, 'frame_end', text='')
        op = row.operator(ZENU_OT_save_time.bl_idname,
                          icon='DOCUMENTS', text='Load')
        op.load = True
        op = row.operator(ZENU_OT_save_time.bl_idname,
                          icon='FILE_TICK', text='Save')
        op.load = False

        row = col.row(align=True)
        row.prop(context.scene, 'frame_start', text='')
        row.prop(context.scene, 'frame_end', text='')


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_setup_render,
    ZENU_OT_set_sample,
    ZENU_OT_set_final_settings,
    ZENU_OT_save_time,
    ZENU_OT_set_preview_settings,
    ZENU_PT_render_settings,
    RenderSettings,
    RenderSetupSettings
))


def register():
    reg()
    bpy.types.Scene.zenu_render_setup = bpy.props.PointerProperty(
        type=RenderSetupSettings)
    bpy.types.Scene.zenu_render_2d = bpy.props.PointerProperty(
        type=RenderSettings)
    bpy.types.Scene.zenu_render_vr = bpy.props.PointerProperty(
        type=RenderSettings)


def unregister():
    unreg()

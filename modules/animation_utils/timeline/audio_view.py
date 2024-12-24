from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Any

import bgl
import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from ....utils import update_window
from ....base_panel import BasePanel


class GpuDrawer(ABC):
    _handler_ds: Any = None
    _handler_ge: Any = None

    @abstractmethod
    def draw(self):
        pass

    def _draw(self):
        pass

    def _register(self):
        if self._handler_ds is not None:
            return

        self._handler_ds = bpy.types.SpaceDopeSheetEditor.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
        self._handler_ge = bpy.types.SpaceGraphEditor.draw_handler_add(self.draw, (), 'WINDOW', 'POST_PIXEL')
        update_window()

    def _unregister(self):
        if self._handler_ds is None:
            return

        bpy.types.SpaceDopeSheetEditor.draw_handler_remove(self._handler_ds, 'WINDOW')
        bpy.types.SpaceGraphEditor.draw_handler_remove(self._handler_ge, 'WINDOW')
        self._handler_ds = None
        update_window()

    def register(self):
        self._register()

    def unregister(self):
        self._unregister()


def get_timeline_audio(context: bpy.types.Context) -> 'TimelineAudio':
    if context.space_data.type == 'GRAPH_EDITOR':
        return context.scene.zenu_timeline_audio_ge
    return context.scene.zenu_timeline_audio_de


class TimelineAudio(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name='Enable', default=False)
    enable_title: bpy.props.BoolProperty(name='Enable Title', default=True)
    enable_title_auto_scale: bpy.props.BoolProperty(name='Enable Title Auto Scale', default=True)
    title_size: bpy.props.FloatProperty(name='Title Size', default=20, min=10, max=100, subtype='FACTOR')
    line_opacity: bpy.props.FloatProperty(name='Line Opacity', default=.3, min=.01, max=1, subtype='FACTOR')
    line_thickness: bpy.props.FloatProperty(name='Line Thickness', default=5)

    symbol_limit: bpy.props.IntProperty(name='Symbol Limit', subtype='FACTOR', min=0, max=1000, default=20)
    offset_y: bpy.props.IntProperty(name='Offset Y', default=100)


class SpacesDrawer(GpuDrawer):
    shader: gpu.types.GPUShader
    batch: gpu.types.GPUBatch
    _spaces: list[tuple[int, int]]

    def __init__(self):
        vert_out = gpu.types.GPUStageInterfaceInfo('my_interface')
        vert_out.smooth('VEC3', 'pos')
        self._spaces = []
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.push_constant('MAT4', 'ModelViewProjectionMatrix')
        shader_info.push_constant('FLOAT', 'opacity')
        shader_info.push_constant('VEC3', "offset")
        shader_info.push_constant('VEC3', "scale")
        shader_info.vertex_in(0, 'VEC3', 'position')
        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, 'VEC4', 'fragColor')

        shader_info.vertex_source(
            'void main()'
            '{'
            '  pos = position;'
            '  gl_Position = ModelViewProjectionMatrix * vec4((position * scale) + offset, 1.0f);'
            '}'
        )

        shader_info.fragment_source(
            'void main()'
            '{'
            '  fragColor = vec4(vec3(pos.x, 1 - pos.x, 0), opacity);'
            '}'
        )

        vertices = (
            (0, 0), (1, 0),
            (0, 1), (1, 1))

        indices = (
            (0, 1, 2), (2, 1, 3))

        shader = gpu.shader.create_from_info(shader_info)
        batch = batch_for_shader(shader, 'TRIS', {'position': vertices}, indices=indices)

        self.shader = shader
        self.batch = batch

    def draw_space(self, start: int, end: int, text: str = None):
        context: bpy.types.Context = bpy.context
        scene = context.scene

        view2d = context.region.view2d
        height = context.region.height

        settings: TimelineAudio = get_timeline_audio(context)

        shader = self.shader
        batch = self.batch
        space_height = settings.line_thickness

        sizey, _ = view2d.view_to_region(0, 0, clip=False)
        sizey2, _ = view2d.view_to_region(10, 0, clip=False)
        scale_y = (sizey2 - sizey) / 1000

        x, y = view2d.view_to_region(start, 1, clip=False)
        x2, y2 = view2d.view_to_region(start + (end - start), 0, clip=False)

        if context.space_data.type == 'GRAPH_EDITOR':
            posx, posy = x, (height - space_height - (settings.offset_y * scale_y)) - (height - y)
        else:
            posx, posy = x, height - space_height - settings.offset_y

        # print()

        if text and settings.enable_title:
            size = settings.title_size

            if settings.enable_title_auto_scale:
                sizey, _ = view2d.view_to_region(0, 0, clip=False)
                sizey2, _ = view2d.view_to_region(10, 0, clip=False)
                size *= 6
                size *= scale_y

            font_id = 0
            blf.color(font_id, 1, 1, 1, 0.6)
            blf.position(font_id, posx, posy - size, 0)
            blf.size(font_id, size)
            blf.draw(font_id, text)

        shader.uniform_float("scale", (x2 - x, space_height, 0))
        shader.uniform_float("offset", (posx, posy, 0))
        shader.uniform_float("opacity", settings.line_opacity)

        # shader.uniform_float("color", (1, 1, 1, .1))
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)

    def draw(self):
        context: bpy.types.Context = bpy.context
        scene = context.scene
        settings: TimelineAudio = get_timeline_audio(context)

        if not hasattr(settings, 'enable'):
            return

        if settings.enable is False:
            return

        if scene.sequence_editor is None:
            return

        strip = scene.sequence_editor.sequences_all

        if strip is None:
            return

        for i in strip:
            name = i.name

            if len(name) > settings.symbol_limit:
                name = name[0:settings.symbol_limit].strip() + '...'

            if i.mute: continue

            self.draw_space(i.frame_final_start, i.frame_final_end, text=name)


ddraw = SpacesDrawer()


def draw(self, context: bpy.types.Context):
    scene = context.scene
    settings: TimelineAudio = get_timeline_audio(context)

    layout = self.layout

    col = layout.column(align=True)
    col.scale_y = 1.5
    col.prop(settings, 'enable', icon='MUTE_IPO_ON')

    col = layout.column(align=True)
    col.scale_y = 1.2

    if not settings.enable: return

    col.prop(settings, 'enable_title', icon='MUTE_IPO_ON')
    if settings.enable_title:
        col.prop(settings, 'enable_title_auto_scale', icon='MUTE_IPO_ON')
        col.prop(settings, 'title_size')

    col = layout.column(align=True)
    col.scale_y = 1.2
    col.prop(settings, 'line_thickness')
    col.prop(settings, 'line_opacity')

    col = layout.column(align=True)
    col.scale_y = 1.2
    col.prop(settings, 'offset_y')
    col.prop(settings, 'symbol_limit')


class ZENU_PT_animation_audio_de(BasePanel):
    bl_label = 'Audio'
    bl_space_type = 'DOPESHEET_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


class ZENU_PT_animation_audio_ge(BasePanel):
    bl_label = 'Audio'
    bl_space_type = 'GRAPH_EDITOR'

    def draw(self, context: bpy.types.Context):
        draw(self, context)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_animation_audio_de,
    ZENU_PT_animation_audio_ge,
    TimelineAudio
))


def register():
    reg()
    bpy.types.Scene.zenu_timeline_audio_de = bpy.props.PointerProperty(type=TimelineAudio)
    bpy.types.Scene.zenu_timeline_audio_ge = bpy.props.PointerProperty(type=TimelineAudio)
    ddraw.register()


def unregister():
    unreg()
    ddraw.unregister()

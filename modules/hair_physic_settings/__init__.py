from typing import Any

import bpy
from ...base_panel import BasePanel


def redraw_all():
    for area in bpy.context.screen.areas:
        area.tag_redraw()


class BakeHairObject:
    particles: list[bpy.types.ParticleSystem]
    point_cache: bpy.types.PointCache = None
    counter: int = 0
    context: bpy.types.Context = None
    is_baking = False

    def __init__(self):
        self.particles = []

    def check_baked(self):
        if self.point_cache is None:
            return None
        if self.point_cache.is_baked:
            self._next_bake()
            return None
        return 2

    def bake(self, particle_system: bpy.types.ParticleSystem):
        override = {
            'scene': self.context.scene,
            'active_object': self.context.object,
            'point_cache': particle_system.point_cache
        }

        with bpy.context.temp_override(**override):
            bpy.ops.ptcache.free_bake()
            bpy.ops.ptcache.bake('INVOKE_DEFAULT', bake=True)

    def _next_bake(self):
        if not self.particles:
            self.is_baking = False
            redraw_all()
            return
        particle = self.particles.pop()
        self.point_cache = particle.point_cache
        self.bake(particle)
        bpy.app.timers.register(self.check_baked)
        self.is_baking = True

    def destroy(self):
        try:
            bpy.app.timers.unregister(self.check_baked)
        except Exception as e:
            pass

    def start_bake(self, object: bpy.types.Object):
        self.particles = list(object.particle_systems)
        self.counter = len(baker.particles)
        self._next_bake()


baker = BakeHairObject()


class ZENU_OT_bake_particle(bpy.types.Operator):
    bl_label = 'Bake All Hair Physic'
    bl_idname = 'zenu.bake_hair_physic'
    bake_all: bpy.props.BoolProperty(default=False)

    @staticmethod
    def bake_particle(context: bpy.types.Context, particle_system: bpy.types.ParticleSystem):
        global point_cache
        override = {
            'scene': context.scene,
            'active_object': context.object,
            'point_cache': particle_system.point_cache
        }

        point_cache = particle_system.point_cache
        with bpy.context.temp_override(**override):
            bpy.ops.ptcache.free_bake()
            bpy.ops.ptcache.bake('INVOKE_DEFAULT', bake=True)

    def execute(self, context: bpy.types.Context):
        baker.context = context
        baker.start_bake(context.active_object)
        return {'FINISHED'}


class ZENU_OT_copy_hair_physic_settings(bpy.types.Operator):
    bl_label = 'Copy Hair Physic Settings'
    bl_idname = 'zenu.hair_settings_copy'
    bl_options = {'REGISTER', 'UNDO'}

    def auto_copy(self, src: Any, dst: Any):
        for key in (i for i in dir(dst) if not i.startswith('_')):
            try:
                setattr(dst, key, getattr(src, key))
            except Exception:
                pass

    def copy_settings(self, dst: bpy.types.ParticleSystem, src: bpy.types.ParticleSystem):
        if src == dst:
            return

        self.auto_copy(dst.point_cache, src.point_cache)
        self.auto_copy(dst.cloth.settings, src.cloth.settings)
        self.auto_copy(dst.settings.effector_weights, src.settings.effector_weights)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        active = obj.particle_systems.active

        for particle in obj.particle_systems:
            self.copy_settings(active, particle)

        return {'FINISHED'}


class ZENU_PT_hair_settings(BasePanel):
    bl_label = 'Hair Settings'
    bl_context = 'objectmode'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object and context.active_object.particle_systems

    def draw_particle_system(self, particle_system: bpy.types.ParticleSystem, layout: bpy.types.UILayout):
        if particle_system.cloth is None:
            return
        cloth_set = particle_system.cloth.settings

        layout = layout.column_flow(align=True)
        layout.prop(particle_system.settings.effector_weights, 'gravity')
        layout.prop(cloth_set, 'mass')
        layout.prop(cloth_set, 'bending_stiffness')
        layout.prop(particle_system.settings, 'bending_random')
        layout.prop(cloth_set, 'bending_damping')

        layout.label(text='Cache')
        layout.prop(particle_system.point_cache, 'frame_start')
        layout.prop(particle_system.point_cache, 'frame_end')

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        obj: bpy.types.Object = context.active_object
        active = obj.particle_systems.active

        if active is None:
            return

        if active.cloth is not None:
            lay = layout.column_flow(align=True)
            lay.operator('ptcache.free_bake_all')
            lay.operator(ZENU_OT_bake_particle.bl_idname)

            if baker.is_baking:
                lay.label(text=f'Baked {baker.counter - len(baker.particles)} / {baker.counter}')

            box = layout.box()
            box.label(text=active.name)
            self.draw_particle_system(obj.particle_systems.active, box)
            box.operator(ZENU_OT_copy_hair_physic_settings.bl_idname)

        layout = layout.box()
        layout.prop(context.scene, 'zenu_ps_show_all', icon='COLLAPSEMENU', text='Show all physic')
        if not context.scene.zenu_ps_show_all:
            return

        for i in obj.particle_systems:
            box = layout.box()
            box.label(text=i.name)
            box.prop(i, 'use_hair_dynamics', icon='STRANDS')

            box = box.column()
            if not i.use_hair_dynamics:
                box.label(text='Dynamic hair not active')
                continue

            self.draw_particle_system(i, box)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_hair_settings,
    ZENU_OT_copy_hair_physic_settings,
    ZENU_OT_bake_particle
))


def register():
    bpy.types.Scene.zenu_ps_show_all = bpy.props.BoolProperty(default=False)
    reg()


def unregister():
    unreg()
    baker.check_baked()

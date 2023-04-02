# TODO: Сделать быстрое создание лоу-поли для мема со скелетом
# TODO: Быстрое создание иерархий коллекций
import bpy
from bpy.types import Context
from ..base_panel import BasePanel
from ..utils import get_modifier, get_collection

LOD_COLLECTION_NAME = 'LOD'


def duplicate_lod(obj: bpy.types.Object):
    mesh = obj.data.copy()
    obj = obj.copy()
    obj.name = obj.name.replace('.001', '_tmp')
    obj.data = mesh
    obj.is_lod = True
    return obj


class ZENU_OT_isolate_with_lods(bpy.types.Operator):
    bl_label = 'Create Lod'
    bl_idname = 'zenu.create_lod'
    bl_options = {"UNDO"}

    def execute(self, context: Context):
        coll = get_collection(LOD_COLLECTION_NAME)
        return {'FINISHED'}


class ZENU_OT_create_lod(bpy.types.Operator):
    bl_label = 'Create Lod'
    bl_idname = 'zenu.create_lod'
    bl_options = {"UNDO"}
    collection: bpy.types.Collection = None
    lod_count: bpy.props.IntProperty()
    fac: bpy.props.FloatProperty(default=.5)

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    @classmethod
    def add_lod(cls, obj: bpy.types.Object):
        cls.collection = get_collection(LOD_COLLECTION_NAME)
        cls.collection.objects.link(obj)

    @classmethod
    def prepare_mesh_with_shape_keys(cls, obj: bpy.types.Object):
        arm = get_modifier(obj, bpy.types.ArmatureModifier)
        arm_name = None
        arm_target = None
        if arm:
            arm_name = arm.name
            arm_target = arm.object

        for mod in obj.modifiers:
            obj.modifiers.remove(mod)
        bpy.ops.object.convert(target='MESH')

        if arm_name:
            mod = obj.modifiers.new(arm_name, 'ARMATURE')
            mod.object = arm_target

    def execute(self, context: Context):
        obj = context.active_object
        obj = duplicate_lod(obj)
        self.add_lod(obj)

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)

        if context.active_object.data.shape_keys:
            self.prepare_mesh_with_shape_keys(context.active_object)

        mod = context.active_object.modifiers.new('Decimate', 'DECIMATE')
        mod.ratio = self.fac
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return {'FINISHED'}


class ZENU_OT_create_lods(bpy.types.Operator):
    bl_label = 'Create Lods'
    bl_idname = 'zenu.create_lods'
    bl_options = {"UNDO"}
    collection: bpy.types.Collection = None
    lod_count: bpy.props.IntProperty()
    fac: bpy.props.FloatProperty(default=.5)

    @classmethod
    def poll(cls, context: 'Context'):
        return context.active_object and isinstance(context.active_object.data, bpy.types.Mesh)

    def create_lod(self, obj: bpy.types.Object, ratio: int, index: int = 0):
        collection = get_collection(LOD_COLLECTION_NAME)

        obj = duplicate_lod(obj)
        obj.name = obj.name.replace('_tmp', '') + f'_LOD{index}'

        collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        mod = bpy.context.active_object.modifiers.new('Decimate', 'DECIMATE')
        mod.ratio = ratio
        return obj

    def execute(self, context: Context):
        obj = context.active_object
        self.create_lod(obj, 1, 0)
        for i in range(1, self.lod_count):
            self.create_lod(obj, 1 - i / self.lod_count, i)
        return {'FINISHED'}


class ZENU_PT_lod_manager(BasePanel):
    bl_label = 'LOD Manager'

    def draw(self, context: Context):
        layout = self.layout
        col = layout.split(align=True)
        col.operator(ZENU_OT_create_lod.bl_idname).fac = .5
        col.operator(ZENU_OT_create_lod.bl_idname, text='0.25').fac = .25

        col = layout.column_flow(align=True)
        col.prop(context.scene, 'lod_count', slider=True)
        col.operator(ZENU_OT_create_lods.bl_idname, text='Create').lod_count = context.scene.lod_count


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_lod_manager,
    ZENU_OT_create_lod,
    ZENU_OT_create_lods
))


def register():
    bpy.types.Collection.is_lod = bpy.props.BoolProperty(default=False)
    bpy.types.Object.is_lod = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.lod_count = bpy.props.IntProperty(default=1, name='LOD Count', min=1, soft_max=10)
    reg()


def unregister():
    unreg()

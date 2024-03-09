import os
import uuid

import bpy
from .export_settings import ExportPointSettings
from ...menu_manager import menu_3d_view, OperatorItem


def export_items(scene, context):
    lst = []

    for i in context.scene.zenu_export_points_settings:
        lst.append((i.uuid, i.name, ''))

    return lst


class ExportPoint(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(subtype='FILE_NAME')
    path: bpy.props.StringProperty(subtype='DIR_PATH')
    settings: bpy.props.EnumProperty(items=export_items)
    uuid: bpy.props.StringProperty()


class ZENU_OT_assign_export_point(bpy.types.Operator):
    bl_label = 'Assign Export Point'
    bl_idname = 'zenu.assign_export_point'
    bl_options = {'UNDO'}

    action: bpy.props.EnumProperty(items=(
        ('ASSIGN', 'Assign', ''),
        ('REMOVE', 'Remove', '')
    ))

    def execute(self, context: bpy.types.Context):
        point = context.scene.zenu_export_points[context.scene.zenu_export_points_index]

        if self.action == 'ASSIGN':
            for i in context.selected_objects:
                i.zenu_export_point = point.uuid
        elif self.action == 'REMOVE':
            for i in context.selected_objects:
                i.zenu_export_point = ''
        return {'FINISHED'}


class ZENU_OT_add_export_point(bpy.types.Operator):
    bl_label = 'Add Export Point'
    bl_idname = 'zenu.add_export_point'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        item = context.scene.zenu_export_points.add()
        item.name = 'File'
        item.uuid = uuid.uuid4().hex
        item.path = os.path.dirname(bpy.data.filepath)
        # print(bpy.data.filepath)
        settings = ExportPointSettings.get_default_export_settings()
        item.settings = settings.uuid

        context.scene.zenu_export_points_index = len(context.scene.zenu_export_points) - 1
        return {'FINISHED'}


class ZENU_OT_select_export_point(bpy.types.Operator):
    bl_label = 'Select Export Point'
    bl_idname = 'zenu.select_export_point'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        point = context.scene.zenu_export_points[context.scene.zenu_export_points_index]

        for i in context.scene.objects:
            i.select_set(i.zenu_export_point == point.uuid)

        return {'FINISHED'}


class ZENU_OT_remove_export_point(bpy.types.Operator):
    bl_label = 'Remove Export Point'
    bl_idname = 'zenu.remove_export_point'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        context.scene.zenu_export_points.remove(context.scene.zenu_export_points_index)

        if context.scene.zenu_export_points_index < 1:
            return {'FINISHED'}

        context.scene.zenu_export_points_index -= 1
        return {'FINISHED'}


class ZENU_OT_export_point(bpy.types.Operator):
    bl_label = 'Export Point'
    bl_idname = 'zenu.export_point'
    export_active: bpy.props.BoolProperty(name='Export Selected In 3D Viewport', default=False)

    @classmethod
    def find_collection(cls, name: str,
                        collection: bpy.types.LayerCollection = None) -> bpy.types.LayerCollection | None:
        collection = collection or bpy.context.view_layer.layer_collection

        for coll in collection.children:
            if coll.name == name:
                return coll

            else:
                return cls.find_collection(name, coll)

        return None

    @classmethod
    def poll(cls, context: bpy.types.Context):
        context = bpy.context
        obj = context.active_object

        point: ExportPoint = None
        for i in context.scene.zenu_export_points:
            if obj.zenu_export_point != i.uuid: continue
            point = i

        return point is not None

    def execute(self, context: bpy.types.Context):
        selected = context.selected_objects
        obj = context.active_object
        point: ExportPoint = None
        if self.export_active:
            for i in context.scene.zenu_export_points:
                if obj.zenu_export_point != i.uuid: continue
                point = i

            if point is None:
                return {'CANCELLED'}
        else:
            point = context.scene.zenu_export_points[context.scene.zenu_export_points_index]

        lst = []
        export_settings = ExportPointSettings.get_by_uuid(point.settings)
        bpy.ops.object.select_all(action='DESELECT')

        if not export_settings:
            return
        collections = {}
        for obj in bpy.data.objects:
            if obj.zenu_export_point != point.uuid: continue

            for collection in obj.users_collection:
                col = self.find_collection(collection.name)

                if col is None: continue
                if collections.get(col): continue

                collections[col] = col.exclude
                col.exclude = False

            lst.append({
                'collections': collections,
                'hide': obj.hide,
                'hide_viewport': obj.hide_viewport,
                'obj': obj
            })

            obj.hide = False
            obj.hide_viewport = False
            obj.select_set(True)

        export_settings = ExportPointSettings.get_by_uuid(point.settings)
        path = os.path.join(point.path, f'{point.name}.fbx')

        bpy.ops.export_scene.fbx(
            use_selection=True,
            bake_anim=export_settings.fbx_bake_animation,
            bake_space_transform=export_settings.fbx_apply_transforms,
            use_armature_deform_only=export_settings.fbx_only_deform_bones,
            add_leaf_bones=export_settings.fbx_use_leaf_bones,
            bake_anim_use_nla_strips=export_settings.fbx_nla_strips,
            bake_anim_use_all_actions=export_settings.fbx_all_actions,
            bake_anim_use_all_bones=export_settings.fbx_key_all_bones,
            bake_anim_force_startend_keying=export_settings.fbx_force_start_end_keying,
            filepath=path
        )

        for i in lst:
            obj = i['obj']
            obj.hide_viewport = i['hide_viewport']
            obj.hide_set(i['hide'])

            for collection, exclude in collections.items():
                collection.exclude = exclude

        bpy.ops.object.select_all(action='DESELECT')

        for obj in selected:
            obj.select_set(True)

        self.report({'INFO'}, f'Exported {path}')

        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_OT_add_export_point,
    ZENU_OT_remove_export_point,
    ZENU_OT_assign_export_point,
    ZENU_OT_select_export_point,
    ZENU_OT_export_point,
    ExportPoint,
))


def text():
    # return 'awdaw'
    context = bpy.context
    obj = context.active_object

    point: ExportPoint = None
    for i in context.scene.zenu_export_points:
        if obj.zenu_export_point != i.uuid: continue
        point = i

    if point is None:
        return 'None'

    return f'Export {point.name}'


def register():
    # pass
    reg()
    #
    bpy.types.Scene.zenu_export_points = bpy.props.CollectionProperty(type=ExportPoint)
    bpy.types.Scene.zenu_export_points_index = bpy.props.IntProperty()

    bpy.types.Object.zenu_export_point = bpy.props.StringProperty(name="UUID")
    menu_3d_view.right.add(OperatorItem(
        op=ZENU_OT_export_point.bl_idname,
        text=text,
        vars={'export_active': True}
    ))


def unregister():
    unreg()

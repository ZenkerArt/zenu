from ctypes.util import test
import json
from pydoc import text

from ..base_ui_list import ZenuUIList
from ...base_panel import BasePanel
from ..events import es
import bpy


@es.on('change_2d')
def on_change_2d(data):
    print('change_2d')


@es.on('change_vr')
def on_change_vr(data):
    print('change_vr')


class TestProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    camera_markers: bpy.props.StringProperty()
    isolate_camera: bpy.props.StringProperty()

    use_in: bpy.props.EnumProperty(items={
        ('VR', 'Use In VR', ''),
        ('2D', 'Use In 2D', ''),
    })


class TestList(ZenuUIList[TestProperty]):
    name = 'test_list'
    _property_group = TestProperty

    def _draw(self, layout, item):
        layout.prop(item, 'name', text='', emboss=False)

    def add(self):
        item = super().add()
        item.name = 'No Name'
        item.camera_markers = '{}'
        return item

    def _on_select(self):
        if bpy.context.scene.zenu_camera_selector_settings.select:
            ZENU_OT_camera_marker.save(self.prev_active)
            ZENU_OT_camera_marker.load()


test_list = TestList()


class CamerasSettings(bpy.types.PropertyGroup):
    select: bpy.props.BoolProperty(name='Load On Select', default=True)


class CameraShots(bpy.types.PropertyGroup):
    shots: bpy.props.StringProperty()


class ZENU_UL_camera_list(bpy.types.UIList):
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', text='', emboss=False)

    def filter_items(self, context: bpy.types.Context, data: bpy.types.AnyType, property: str):
        items = getattr(data, property)
        filtered = [0] * len(items)
        for index, obj in enumerate(items):
            obj: bpy.types.Object
            if obj.data is None:
                continue

            if not isinstance(obj.data, bpy.types.Camera):
                continue

            filtered[index] = self.bitflag_filter_item
        ordered = []

        return filtered, ordered


class ZENU_OT_camera_marker(bpy.types.Operator):
    bl_label = 'Camera Marker'
    bl_idname = 'zenu.camera_marker'
    bl_options = {'UNDO'}

    action: bpy.props.EnumProperty(items=(
        ('SAVE', 'Save', ''),
        ('LOAD', 'Load', ''),
        ('CLEAR', 'Clear', ''),
    ))

    @staticmethod
    def save(item: TestProperty = None):
        scene = bpy.context.scene
        if item is None:
            item = test_list.active

        if not item:
            return

        if item.isolate_camera != '':
            return

        lst = []
        for marker in scene.timeline_markers:
            marker: bpy.types.TimelineMarker

            if marker.camera is not None:
                lst.append({
                    'camera': marker.camera.name,
                    'frame': marker.frame,
                    'name': marker.name
                })
        item.camera_markers = json.dumps(lst)

    @staticmethod
    def isolate(camera_name: str):
        item = test_list.active
        camera = bpy.data.objects.get(camera_name)

        if camera is None:
            return

        if item.isolate_camera == '':
            ZENU_OT_camera_marker.save()

        if item.isolate_camera == camera_name:
            item.isolate_camera = ''
            ZENU_OT_camera_marker.load()
        else:
            item.isolate_camera = camera_name
            ZENU_OT_camera_marker.clear()
            bpy.context.scene.camera = camera

    @staticmethod
    def load():
        scene = bpy.context.scene
        item = test_list.active

        try:
            data = json.loads(item.camera_markers)
        except Exception as e:
            print('Error', e)
            return

        if not item:
            return

        if item.isolate_camera != '':
            ZENU_OT_camera_marker.clear()
            bpy.context.scene.camera = bpy.data.objects.get(
                item.isolate_camera)
            return

        ZENU_OT_camera_marker.clear()

        for marker in data:
            marker: bpy.types.TimelineMarker

            camera = bpy.data.objects.get(marker['camera'])

            if camera is None:
                continue

            marker_new = scene.timeline_markers.new(marker['name'])
            marker_new.frame = marker['frame']
            marker_new.camera = camera
            marker_new.select = False

    @staticmethod
    def clear():
        scene = bpy.context.scene
        for marker in scene.timeline_markers:
            if marker.camera is not None:
                scene.timeline_markers.remove(marker)

    def execute(self, context: bpy.types.Context):
        match self.action:
            case 'SAVE':
                self.save()
            case 'LOAD':
                self.load()
            case 'CLEAR':
                self.clear()
        return {'FINISHED'}


class ZENU_OT_camera_selector_actions(bpy.types.Operator):
    bl_label = 'Camera Selector Actions'
    bl_idname = 'zenu.camera_selector_actions'
    bl_options = {'UNDO'}
    action: bpy.props.EnumProperty(items=(
        ('SELECT', 'Select', ''),
        ('ISOLATE', 'Isolate', ''),
    ))
    camera: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        item = test_list.active
        camera = bpy.data.objects.get(self.camera)

        if camera is None:
            return {'FINISHED'}

        match self.action:
            case 'SELECT':
                pass
            case 'ISOLATE':
                ZENU_OT_camera_marker.isolate(camera_name=camera.name)

        return {'FINISHED'}


class ZENU_PT_camera_selector(BasePanel):
    bl_label = "Camera Selector"
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene

        test_list.draw_ui(layout=layout)

        col = layout.column(align=True)
        col.prop(scene.zenu_camera_selector_settings,
                 'select', icon='CHECKBOX_HLT')

        row = col.row(align=True)
        op = row.operator(ZENU_OT_camera_marker.bl_idname,
                          text='Save', icon='FILE_TICK')
        op.action = 'SAVE'
        op = row.operator(ZENU_OT_camera_marker.bl_idname,
                          text='Load', icon='PACKAGE')
        op.action = 'LOAD'
        op = row.operator(ZENU_OT_camera_marker.bl_idname,
                          text='Clear', icon='X')
        op.action = 'CLEAR'

        item = test_list.active
        if item is None:
            return

        data = json.loads(item.camera_markers)
        cameras = {i['camera'] for i in data}
        col = layout.column(align=True)
        for camera in cameras:
            if bpy.data.objects.get(camera) is None:
                continue

            scene_camera_name = ''

            if scene.camera:
                scene_camera_name = scene.camera.name

            row = col.row(align=True)
            op = row.operator(ZENU_OT_camera_selector_actions.bl_idname,
                              text=camera, icon='RESTRICT_SELECT_OFF', depress=camera == scene_camera_name)
            op.action = 'SELECT'
            op.camera = camera

            op = row.operator(ZENU_OT_camera_selector_actions.bl_idname, text='',
                              icon='OBJECT_HIDDEN', depress=camera == item.isolate_camera)
            op.action = 'ISOLATE'
            op.camera = camera


reg, unreg = bpy.utils.register_classes_factory((
    CamerasSettings,
    CameraShots,
    ZENU_OT_camera_selector_actions,
    ZENU_PT_camera_selector,
    ZENU_OT_camera_marker,
    ZENU_UL_camera_list,
))


def register():
    reg()
    test_list.register()
    bpy.types.Scene.zenu_camera_selector_settings = bpy.props.PointerProperty(
        type=CamerasSettings)


def unregister():
    unreg()
    test_list.unregister()

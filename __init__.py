from threading import Timer

from bpy.types import PropertyGroup
from .modules import modules
from .keybindings import key_spaces
from bpy.app.handlers import persistent
import bpy

bl_info = {
    "name": "Zenu",
    "author": "Zenker",
    "description": "",
    "blender": (4, 0, 0),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}

modules_name = {i.__name__: i for i in modules}


class MATERIAL_UL_ZENU_modules(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        slot = item

        layout.prop(slot, 'name', text='', emboss=False)
        layout.prop(slot, 'is_enable',
                    text='', icon='HIDE_OFF' if slot.is_enable else 'HIDE_ON',
                    emboss=False)


def register_modules():
    # bpy.context.scene.zenu_modules.clear()

    for i in modules:
        name = i.__name__
        text = ' '.join(name.rsplit('.', maxsplit=1)[1].split('_')).title()
        item = bpy.context.scene.zenu_modules.get(text)

        if item:
            if not item.is_enable:
                modules_name[name].unregister()
            continue

        item: ZenuModule = bpy.context.scene.zenu_modules.add()
        item.name = text
        item.path = name


def update(self, context):
    if self.is_enable:
        modules_name[self.path].register()
    else:
        modules_name[self.path].unregister()
    # print(self.path, modules_name[self.path])


class ZenuModule(PropertyGroup):
    name: bpy.props.StringProperty(name='Module Name')
    path: bpy.props.StringProperty(name='Module Path')
    is_enable: bpy.props.BoolProperty(name='Module Is Enable', default=True, update=update)


class ZenUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout

        layout.template_list("MATERIAL_UL_ZENU_modules", "", context.scene, "zenu_modules", context.scene,
                             "zenu_modules_active")


@persistent
def on_change_file():
    Timer(.2, register_modules, ()).start()
    print('File load')


def register():
    for i in key_spaces:
        i.register()

    for i in modules:
        try:
            i.register()
        except Exception:
            pass
    bpy.utils.register_class(ZenuModule)
    bpy.utils.register_class(ZenUtilsPreferences)
    bpy.utils.register_class(MATERIAL_UL_ZENU_modules)

    bpy.types.Scene.zenu_modules = bpy.props.CollectionProperty(name='Zenu Modules', type=ZenuModule)
    bpy.types.Scene.zenu_modules_active = bpy.props.IntProperty(name='Active Module')
    Timer(.2, register_modules, ()).start()
    bpy.app.handlers.load_post.append(on_change_file)


def unregister():
    for i in key_spaces:
        i.unregister()

    for i in modules:
        try:
            i.unregister()
        except Exception:
            pass
    bpy.utils.unregister_class(ZenuModule)
    bpy.utils.unregister_class(ZenUtilsPreferences)
    bpy.utils.unregister_class(MATERIAL_UL_ZENU_modules)
    try:
        bpy.app.handlers.load_post.remove(on_change_file)
    except Exception:
        pass

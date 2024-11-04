import bpy


def get_name(self):
    return self.obj.name


def set_name(self, text: str):
    self.obj.name = text


class AudioTrigger(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='', get=get_name, set=set_name)
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    radius: bpy.props.FloatProperty(default=.01)
    path: bpy.props.StringProperty(subtype='DIR_PATH')
    shape: bpy.props.EnumProperty(items=(
        ('Sphere', 'SPHERE', ''),
    ))


class AudioTriggerPoint(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='', get=get_name, set=set_name)
    obj: bpy.props.PointerProperty(type=bpy.types.Object)
    shape: bpy.props.EnumProperty(items=(
        ('Point', 'POINT', ''),
    ))

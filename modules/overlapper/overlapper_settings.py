import bpy


class OverlapperSettings(bpy.types.PropertyGroup):
    stiffness: bpy.props.FloatProperty(
        default=40, name='Stiffness', min=0, soft_max=50, subtype='FACTOR')
    damping: bpy.props.FloatProperty(
        default=7, name='Damping', min=0, soft_max=25, subtype='FACTOR')

    only_root_motion: bpy.props.BoolProperty(
        name='Only Root', description='Take only root motion', default=True)
    motion_multiply: bpy.props.FloatProperty(
        default=10, name='Motion Influence', min=0, soft_max=10, subtype='FACTOR')

    wind: bpy.props.FloatVectorProperty(subtype='XYZ')

    bake_offset: bpy.props.IntProperty(default=0, name='Bake Offset', min=0)
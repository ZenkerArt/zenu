import bpy
from ...utils import get_path_to_asset, get_collection


class ShapesEnum:
    SphereEmpty = 'WGT-SphereEmpty'
    SphereDirWire = 'WGT-SphereDirWire'
    Sphere = 'WGT-Sphere'
    PlaneWireBevel = 'WGT-PlaneWireBevel'
    PlaneWire = 'WGT-PlaneWire'
    Eye = 'WGT-Eye'
    Cylinder = 'WGT-Cylinder'
    CubeWire = 'WGT-CubeWire'
    CircleWireX2 = 'WGT-CircleWireX2'
    CircleWireX = 'WGT-CircleWireX'
    CircleWirePevis = 'WGT-CircleWirePevis'
    CircleWirePackMan = 'WGT-CircleWirePackMan'
    CircleWire1 = 'WGT-CircleWire1'
    Brow = 'WGT-Brow'
    ArrowTwoSide = 'WGT-ArrowTwoSide'
    Arrow = 'WGT-Arrow'


def get_shape(name: str) -> bpy.types.Object | None:
    path = get_path_to_asset('ZenuRigAssets.blend')
    collection = get_collection('RIG_SHAPES')
    collection.hide_viewport = True
    collection.hide_render = True
    obj = collection.objects.get(name)

    if obj is not None:
        return obj

    with bpy.data.libraries.load(path) as (data_from, data_to):
        data_to.objects = [name]

    collection.objects.link(data_to.objects[0])
    obj = data_to.objects[0]

    for mod in obj.modifiers:
        obj: bpy.types.Object
        if mod.name.startswith('[REMOVE]'):
            obj.modifiers.remove(mod)

    return obj

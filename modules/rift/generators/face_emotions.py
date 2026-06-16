from dataclasses import dataclass

import bpy.types

from ..rig_generator import RigGenerator

SHAPE_CONTROL = 'CTR_ShapesList'


@dataclass
class RiftShapes:
    cl: str
    op: str = None


class GeneratorFaceEmotion(RigGenerator):
    def get_custom_property(self, name: str):
        pb = self.get_pose_bone(SHAPE_CONTROL)
        prop = pb.get(name)

        if prop is not None:
            return f'pose.bones["{SHAPE_CONTROL}"]["{name}"]'

        pb[name] = 0.0
        ui = pb.id_properties_ui(name)

        ui.update(
            min=0.0,
            max=1.0,
            soft_min=0.0,
            soft_max=1.0,
            # description="My custom value",
            subtype='FACTOR'
        )

        return f'pose.bones["{SHAPE_CONTROL}"]["{name}"]'

    def execute(self, context: bpy.types.Context):

        obj = self.get_obj()

        self.start_edit()

        bone = self.get_edit_bone(self.dup_bone('SHAPES_', 'cf_J_FaceRoot'))

        bone.name = SHAPE_CONTROL

        bone.head.x += .1
        bone.tail.x += .1

        self.end_edit()

        objects: list[bpy.types.Object] = []
        for obj_mod in bpy.data.objects.values():
            obj_mod: bpy.types.Object
            if not isinstance(obj_mod.data, bpy.types.Mesh): continue

            if obj_mod.data.shape_keys is None:
                continue

            for mod in obj_mod.modifiers.values():
                mod: bpy.types.ArmatureModifier
                if isinstance(mod, bpy.types.ArmatureModifier) and mod.object == obj:
                    objects.append(obj_mod)

        for i in objects:
            shapes = i.data.shape_keys
            if shapes is None: continue

            for shape_cl in shapes.key_blocks:
                shape_name = shape_cl.name.split('.', maxsplit=1)[-1]
                shape_cl.name = shape_name

        cl_shapes: list[RiftShapes] = []

        for i in objects:
            shapes = i.data.shape_keys.key_blocks

            for shape_cl in shapes:
                if '_sita' in shape_cl.name: continue

                if '_cl' in shape_cl.name:
                    op = shape_cl.name.replace('_cl', '_op').strip()
                    rift_shape = RiftShapes(
                        cl=shape_cl.name,
                    )

                    if shapes.get(op) is not None:
                        rift_shape.op = op

                    cl_shapes.append(rift_shape)

        for op in cl_shapes:
            prop_path = self.get_custom_property(op.cl.replace('_cl', ''))
            for i in objects:
                shapes = i.data.shape_keys.key_blocks
                shape_cl: bpy.types.ShapeKey = shapes.get(op.cl)

                if shape_cl is None: continue

                def create_driver(sh, exp: str):
                    driver = sh.driver_add('value').driver
                    var = driver.variables.new()
                    var.name = 'var'
                    var.type = 'SINGLE_PROP'

                    target = var.targets[0]
                    target.id = obj
                    target.data_path = prop_path

                    driver.type = 'SCRIPTED'
                    driver.expression = exp

                create_driver(shape_cl, 'var')


                if op.op is None: continue

                shape_op: bpy.types.ShapeKey = shapes.get(op.op)

                if shape_op is not None:
                    create_driver(shape_op, '1 - var if var > .0001 else 0')

        self.update(context)

    def update(self, context: bpy.types.Context):

        obj = self.get_obj()

        self.start_edit()
        self.end_edit()

        objects: list[bpy.types.Object] = []
        for obj_mod in bpy.data.objects.values():
            obj_mod: bpy.types.Object
            if not isinstance(obj_mod.data, bpy.types.Mesh): continue

            if obj_mod.data.shape_keys is None:
                continue

            for mod in obj_mod.modifiers.values():
                mod: bpy.types.ArmatureModifier
                if isinstance(mod, bpy.types.ArmatureModifier) and mod.object == obj:
                    objects.append(obj_mod)

        for obj in objects:
            if obj.data.shape_keys and obj.data.shape_keys.animation_data:
                for fc in obj.data.shape_keys.animation_data.drivers:
                    drv = fc.driver
                    drv.expression = drv.expression

        bpy.context.view_layer.update()

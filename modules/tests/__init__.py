import bpy
from bpy.app.handlers import persistent
from mathutils import Vector, Quaternion
from .shapes import DrawTest, DrawObj
from ...base_panel import BasePanel
import test_physic
from test_physic import PyVector

phy = test_physic.Physic()
objs: list['ObjBall'] = []
test = DrawTest()
empty_bind = None

class ObjBall:
    ball: test_physic.RigidBodyObj
    obj: DrawObj

    def __init__(self, ball: test_physic.RigidBodyObj, obj: DrawObj):
        self.ball = ball
        self.obj = obj

    def apply_physic(self):
        trans = phy.get_rigid_obj_transforms(self.ball)

        self.obj.pos = Vector(trans.position.to_blender())


class ZENU_OT_add_object(bpy.types.Operator):
    bl_label = 'Add Object'
    bl_idname = 'zenu.add_object'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        # bpy.ops.object.create
        objs.append(ObjBall(
            phy.create_rigid_obj((0, 10, 0)),
            test.add_draw_obj(Vector((0, 10, 0)))
        ))
        return {'FINISHED'}


class ZENU_OT_add_cube(bpy.types.Operator):
    bl_label = 'Add Cube'
    bl_idname = 'zenu.add_cube'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        # bpy.ops.object.create
        for x in range(0, 10):
            for y in range(0, 10):
                for z in range(0, 10):
                    objs.append(ObjBall(
                        phy.create_rigid_obj((x, y, z)),
                        test.add_draw_obj(Vector((x, y, z)))
                    ))
        return {'FINISHED'}

class ZENU_OT_add_constraint(bpy.types.Operator):
    bl_label = 'Add Constraint'
    bl_idname = 'zenu.add_constraint'
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        ob = empty_bind
        settings = test_physic.RigidBodyObjSettings(
            dump=.1,
            mass=.5
        )
        # bpy.types.Scene.ph_dump = bpy.props.FloatProperty(name='Dump')
        # bpy.types.Scene.ph_stiffness = bpy.props.BoolProperty(name='Stiffness')
        # bpy.types.Scene.ph_sprint = bpy.props.BoolProperty(name='Sprint')
        dump = bpy.props.FloatProperty(name='Dump')
        stiffness = bpy.props.FloatProperty(name='Stiffness')
        sprint = bpy.props.FloatProperty(name='Sprint')
        for i in range(0, 10):
            ob1 = phy.create_rigid_obj((i, 0, 0), settings)

            phy.add_spherical_joint(ob1, ob, 1, 50, 20)

            objs.append(ObjBall(
                ob1,
                test.add_draw_obj(Vector((i, 0, 0)))
            ))

            ob = ob1

        return {'FINISHED'}

class ZENU_OT_physic_step(bpy.types.Operator):
    bl_label = 'Physic Clear'
    bl_idname = 'zenu.physic_step'

    def execute(self, context: bpy.types.Context):
        global phy
        phy = test_physic.Physic()
        objs.clear()
        test.clear()

        global empty_bind
        ll = bpy.data.objects['Empty'].location
        empty_bind = phy.create_rigid_kinematic_obj((ll.x, ll.z, ll.y))
        objs.append(ObjBall(
            empty_bind,
            test.add_draw_obj(ll)
        ))
        return {'FINISHED'}


class ZENU_PT_tests(BasePanel):
    bl_label = 'Tests'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(context.active_object, 'is_rigid_obj')
        layout.prop(context.scene, 'ground_target')
        layout.label(text=f'Object Count {len(objs)}')
        box = layout.box()
        box.alert = True
        box.operator(ZENU_OT_physic_step.bl_idname)
        box.operator(ZENU_OT_add_object.bl_idname, icon_value=0)
        box.operator(ZENU_OT_add_cube.bl_idname)
        box.operator(ZENU_OT_add_constraint.bl_idname)


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_tests,
    ZENU_OT_physic_step,
    ZENU_OT_add_object,
    ZENU_OT_add_cube,
    ZENU_OT_add_constraint
))

@persistent
def update(scene):
    ll = bpy.data.objects['Empty'].location


    obj: bpy.types.Object = scene.ground_target
    v = obj.location
    r = obj.rotation_euler
    phy.set_ground_position(test_physic.PyVector(v.x, v.z, v.y))
    phy.set_ground_rotation(test_physic.PyVector(-r.x, -r.z, -r.y))
    if empty_bind:
        phy.set_position_kinematic(empty_bind, PyVector(ll.x, ll.z, ll.y))
    for ob in objs:
        ob.apply_physic()

    phy.step()

# test.add_draw_obj(Vector((0, 0, 2)))


def register():
    bpy.types.Scene.ph_dump = bpy.props.FloatProperty(name='Dump')
    bpy.types.Scene.ph_stiffness = bpy.props.BoolProperty(name='Stiffness')
    bpy.types.Scene.ph_sprint = bpy.props.BoolProperty(name='Sprint')

    bpy.types.Object.is_rigid_obj = bpy.props.BoolProperty(name='Is Rigid Object')
    bpy.types.Scene.ground_target = bpy.props.PointerProperty(type=bpy.types.Object)
    reg()
    # bpy.app.handlers.frame_change_pre.append(update)
    # test.register()


def unregister():
    unreg()
    # bpy.app.handlers.frame_change_pre.remove(update)
    # test.unregister()

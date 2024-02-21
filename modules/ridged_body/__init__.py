from threading import Thread
from timeit import Timer

import bpy
from ...base_panel import BasePanel

progress = 0


class ConnectRigidBodies(bpy.types.Operator):
    '''Create rigid body constraints between selected rigid bodies'''
    bl_idname = "zenu.connect_ridget_bodes"
    bl_label = "Connect Rigid Bodies"
    bl_options = {'REGISTER', 'UNDO'}
    con_type: bpy.props.EnumProperty(
        name="Type",
        description="Type of generated constraint",
        # XXX Would be nice to get icons too, but currently not possible ;)
        items=tuple((e.identifier, e.name, e.description, e.value)
                    for e in bpy.types.RigidBodyConstraint.bl_rna.properties["type"].enum_items),
        default='FIXED',
    )
    pivot_type: bpy.props.EnumProperty(
        name="Location",
        description="Constraint pivot location",
        items=(('CENTER', "Center", "Pivot location is between the constrained rigid bodies"),
               ('ACTIVE', "Active", "Pivot location is at the active object position"),
               ('SELECTED', "Selected", "Pivot location is at the selected object position")),
        default='CENTER',
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.rigid_body)

    def _add_constraint(self, context, object1, object2):
        if object1 == object2:
            return

        loc = (object1.location + object2.location) / 2.0

        ob = bpy.data.objects.new("Constraint", object_data=None)
        ob.location = loc
        context.scene.collection.objects.link(ob)
        # context.view_layer.objects.active = ob
        # ob.select = True

        # bpy.ops.rigidbody.constraint_add()

        # con_obj = context.view_layer.objects.active
        # con_obj.empty_display_type = 'ARROWS'
        # con = ob.rigid_body_constraint
        # con.type = 'FIXED'
        #
        # con.object1 = object1
        # con.object2 = object2

    def thread(self, context, objs_sorted):
        # print(dir(context))
        for i in range(1, len(objs_sorted)):
            self._add_constraint(context, objs_sorted[i - 1], objs_sorted[i])

    # def modal(self, context, event):
    #     if event.type == 'MOUSEMOVE':  # Apply
    #         pass
    #     elif event.type == 'LEFTMOUSE':  # Confirm
    #         return {'FINISHED'}
    #     elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
    #         return {'CANCELLED'}
    #
    #     return {'RUNNING_MODAL'}
    #
    # def invoke(self, context, event):
    #     self.execute(context)
    #
    #     context.window_manager.modal_handler_add(self)
    #     return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene
        objects = context.selected_objects
        obj_act = context.active_object
        change = True

        objs_sorted = [obj_act]
        objects_tmp = context.selected_objects
        try:
            objects_tmp.remove(obj_act)
        except ValueError:
            pass

        last_obj = obj_act

        while objects_tmp:
            objects_tmp.sort(key=lambda o: (last_obj.location - o.location).length)
            last_obj = objects_tmp.pop(0)
            objs_sorted.append(last_obj)
        #
        self.thread(context, objs_sorted)
        # Thread(target=self.thread, args=(context, objs_sorted)).start()
        if change:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                obj.select = True

            context.view_layer.objects.active = obj_act
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No other objects selected")
            return {'CANCELLED'}


class Test(bpy.types.Operator):
    '''Create rigid body constraints between selected rigid bodies'''
    bl_idname = "zenu.test"
    bl_label = "Test"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        for ob in context.selected_objects:
            t = Timer()
            # ob_copy = bpy.data.objects.new("Constraint", object_data=None)
            ob_copy = ob.copy()
            context.scene.collection.objects.link(ob_copy)
            # context.view_layer.objects.active = ob_copy
            # ob_copy.select_set(True)

            print(t.timeit())

        return {'FINISHED'}


class ZENU_PT_ridged_body(BasePanel):
    bl_label = 'Ridged Body'
    bl_context = ''

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(ConnectRigidBodies.bl_idname)
        layout.operator(Test.bl_idname)
        layout.label(text=f'progress {progress}')
        # layout.prop(context.scene, 'zenu_progress')


reg, unreg = bpy.utils.register_classes_factory((
    ConnectRigidBodies,
    Test,
    ZENU_PT_ridged_body
))


def register():
    bpy.types.Scene.zenu_progress = bpy.props.FloatProperty('Test', default=0)
    reg()


def unregister():
    unreg()

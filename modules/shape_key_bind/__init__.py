import bpy
from ...base_panel import BasePanel, BasePanelOnlyArmature
from ...utils import get_modifier

objects: list[bpy.types.Object] = []
VarList = list[tuple[bpy.types.FCurve, bpy.types.DriverVariable]]


def find_variables(obj: bpy.types.Object) -> VarList:
    var = []

    try:
        if obj.data.shape_keys.animation_data is None:
            return var
    except Exception:
        return []

    shape_key: bpy.types.ShapeKey = obj.active_shape_key

    for d in obj.data.shape_keys.animation_data.drivers:
        d: bpy.types.FCurve

        if shape_key.name not in d.data_path:
            continue

        for i in d.driver.variables:
            if i.type != 'TRANSFORMS':
                continue
            var.append((d, i))
    return var


class ZENU_UL_shape_key_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, 'name', emboss=False, text='')
        layout.prop(item, 'value', emboss=False, text='')


class ZENU_PT_bind_shape_key(BasePanelOnlyArmature):
    bl_label = 'Bind Shape Key'
    bl_context = ''
    bl_region_type = 'UI'
    def draw_driver(self, driver_vars: VarList):
        layout = self.layout
        for _, var in driver_vars:
            if var.type != 'TRANSFORMS':
                continue
            target = var.targets[0]
            box = layout.box()
            box.label(text=var.name)
            col = box.column(align=True)
            col.prop(target, 'transform_space', text='')
            col.prop(target, 'transform_type', text='')

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column_flow(align=True)
        obj: bpy.types.Object = bpy.data.objects.get(ZENU_OT_select_object.active_obj)
        bone: bpy.types.PoseBone = context.active_pose_bone

        if obj is not None:
            vars = find_variables(obj)
            is_press = False
            driver = None
            for fcurve, var in find_variables(obj):
                if var.targets[0].bone_target == bone.name:
                    is_press = True
                    driver = fcurve

            layout.template_list('ZENU_UL_shape_key_list', '', obj.data.shape_keys,
                                 'key_blocks', obj,
                                 'active_shape_key_index')

            layout.prop(obj, 'show_only_shape_key')

            lay = layout.row(align=True)
            op = lay.operator(ZENU_OT_bind_shape_key_to_bone.bl_idname, depress=is_press)
            op.invert = False
            op.obj = obj.name

            op = lay.operator(ZENU_OT_bind_shape_key_to_bone.bl_idname, text='Invert', depress=is_press)
            op.invert = True
            op.obj = obj.name

            lay = layout.column_flow(align=True)
            op = lay.operator(ZENU_OT_shape_key_bind_custom_exp.bl_idname, text='Div / .085')
            op.obj = obj.name
            op.expression = '$value / .085'

            op = lay.operator(ZENU_OT_shape_key_bind_custom_exp.bl_idname, text='Div / .0425')
            op.obj = obj.name
            op.expression = '$value / .0425'

            layout.operator(ZENU_OT_duplicate_shape_key.bl_idname)

            if driver:
                layout.prop(driver.driver, 'expression', text='')

            self.draw_driver(vars)

        for obj in objects:
            op = col.operator(ZENU_OT_select_object.bl_idname, text=obj.name,
                              depress=obj.name == ZENU_OT_select_object.active_obj)
            op.obj = obj.name


class ZENU_OT_select_object(bpy.types.Operator):
    bl_label = 'Select Object'
    bl_idname = 'zenu.select_object'
    obj: bpy.props.StringProperty()
    active_obj: str = ''

    def execute(self, context: bpy.types.Context):
        ZENU_OT_select_object.active_obj = self.obj

        return {'FINISHED'}


class ZENU_OT_duplicate_shape_key(bpy.types.Operator):
    bl_label = 'Duplicate Shape Key'
    bl_idname = 'zenu.duplicate_shape_key'

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        obj.show_only_shape_key = True
        bpy.ops.object.shape_key_add(from_mix=True)
        obj.show_only_shape_key = False
        return {'FINISHED'}


class ZENU_OT_bind_shape_key_to_bone(bpy.types.Operator):
    bl_label = 'Shape Key bind'
    bl_idname = 'zenu.shape_key_bind'
    obj: bpy.props.StringProperty()
    invert: bpy.props.BoolProperty()

    def execute(self, context: bpy.types.Context):
        obj = bpy.data.objects.get(self.obj)
        bone = context.active_pose_bone
        var_name = 'shapebind'

        if obj is None or bone is None:
            return {'CANCELLED'}

        shape_key: bpy.types.ShapeKey = obj.active_shape_key
        drivers = find_variables(obj)
        for fcurve, var in drivers:
            if var.targets[0].bone_target == bone.name:
                if len(drivers) <= 1:
                    shape_key.driver_remove('value')
                    return {'CANCELLED'}
                fcurve.driver.variables.remove(var)
                return {'CANCELLED'}

        driver_curve = shape_key.driver_add('value')
        var = driver_curve.driver.variables.new()

        var.name = var_name
        target = var.targets[0]
        target.id = context.active_object
        target.bone_target = bone.name

        var.type = 'TRANSFORMS'
        target.transform_type = 'LOC_Y'
        target.transform_space = 'LOCAL_SPACE'
        if self.invert:
            driver_curve.driver.expression = f'1 - {var_name}'
        else:
            driver_curve.driver.expression = var_name

        return {'FINISHED'}


class ZENU_OT_shape_key_bind_custom_exp(bpy.types.Operator):
    bl_label = 'Shape Key bind'
    bl_idname = 'zenu.shape_key_bind_custom_exp'
    obj: bpy.props.StringProperty()
    expression: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        obj = bpy.data.objects.get(self.obj)
        bone = context.active_pose_bone
        var_name = 'shapebind'

        if obj is None or bone is None:
            return {'CANCELLED'}

        shape_key: bpy.types.ShapeKey = obj.active_shape_key
        drivers = find_variables(obj)
        for fcurve, var in drivers:
            if var.targets[0].bone_target == bone.name:
                if len(drivers) <= 1:
                    shape_key.driver_remove('value')
                    return {'CANCELLED'}
                fcurve.driver.variables.remove(var)
                return {'CANCELLED'}

        driver_curve = shape_key.driver_add('value')
        var = driver_curve.driver.variables.new()

        var.name = var_name
        target = var.targets[0]
        target.id = context.active_object
        target.bone_target = bone.name

        var.type = 'TRANSFORMS'
        target.transform_type = 'LOC_Y'
        target.transform_space = 'LOCAL_SPACE'

        driver_curve.driver.expression = self.expression.replace('$value', var_name)

        return {'FINISHED'}


class ZENU_OT_open_bind_shape_key(bpy.types.Operator):
    bl_label = 'Open Bind Shape Key'
    bl_idname = 'zenu.open_bind_shape_key'

    def execute(self, context: bpy.types.Context):
        objects.clear()
        for obj in bpy.data.objects:
            mod: bpy.types.ArmatureModifier = get_modifier(obj, bpy.types.ArmatureModifier)
            if mod is None:
                continue
            if context.active_object == mod.object:
                objects.append(obj)

        bpy.ops.wm.call_panel(name='ZENU_PT_bind_shape_key')
        return {'FINISHED'}


reg, unreg = bpy.utils.register_classes_factory((
    ZENU_PT_bind_shape_key,
    ZENU_OT_open_bind_shape_key,
    ZENU_OT_select_object,
    ZENU_OT_bind_shape_key_to_bone,
    ZENU_OT_shape_key_bind_custom_exp,
    ZENU_OT_duplicate_shape_key,
    ZENU_UL_shape_key_list
))


def register():
    reg()


def unregister():
    unreg()

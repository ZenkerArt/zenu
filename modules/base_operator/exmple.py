class RigActions(ActionOperator):
    bl_label = 'Rig Action'
    mute: bpy.props.BoolProperty(default=True)

    # Convert to op.action = 'back'
    def action_back(self, context: bpy.types.Context):
        pass

def draw(layout):
    row = layout.row()
    RigActions.draw_action(row, RigActions.action_back, 'Back')

reg, unreg = bpy.utils.register_classes_factory((
    RigActions.gen_op(),
))
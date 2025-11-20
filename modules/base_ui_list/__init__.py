from typing import Any, Callable, Generic, TypeVar
import bpy

T = TypeVar('T')


class BaseListAction:
    ADD = 'ADD'
    REMOVE = 'REMOVE'
    UP = 'UP'
    DOWN = 'DOWN'

    MOVE = 'MOVE'


class ZENU_UL_base_list(bpy.types.UIList):
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname):
        self.custom_draw(layout, item)


class ZENU_OT_base_list_actions(bpy.types.Operator):
    bl_label = 'Base List Actions'
    bl_idname = 'zenu.base_list_actions'
    bl_options = {'UNDO'}
    owner: 'ZenuUIList'

    action: bpy.props.EnumProperty(items=(
        (BaseListAction.ADD, 'Add', ''),
        (BaseListAction.REMOVE, 'Remove', ''),
        (BaseListAction.UP, 'Up', ''),
        (BaseListAction.DOWN, 'Down', ''),
    ))

    _active_prop_name: str
    _property_list_name: str
    _lst: ZENU_UL_base_list

    def execute(self, context: bpy.types.Context):
        index = self.owner.index

        match self.action:
            case BaseListAction.ADD:
                self.owner.add()
            case BaseListAction.REMOVE:
                self.owner.remove(index)
            case BaseListAction.UP:
                self.owner.move(index, index - 1)
            case BaseListAction.DOWN:
                self.owner.move(index, index + 1)

        return {'FINISHED'}


class ZenuUIList(Generic[T]):
    name: str = None
    _property_group: bpy.types.PropertyGroup = None
    _active_path: Any = bpy.types.Scene
    _reg: Callable
    _unreg: Callable

    _op: ZENU_OT_base_list_actions
    _ui_list: ZENU_UL_base_list

    _active_prop_name: str
    _property_list_name: str

    _ui_list_name: str
    _op_idname: str
    _prev_active: int = None

    _index: int = 0

    def __init__(self):
        assert self.name is not None
        assert self._property_group is not None
        self._active_prop_name = f'zenu_autogen_{self.name}_active'
        self._property_list_name = f'zenu_autogen_{self.name}_property_list'

        idname = f'{self.name}_actions'
        op_name = f'ZENU_OT_AUTOGEN_{idname}'

        self._op_idname = 'zenu.' + idname

        actions = type(op_name, (ZENU_OT_base_list_actions,), {
            'bl_idname': self._op_idname,
            '_active_prop_name': self._active_prop_name,
            '_property_list_name': self._property_list_name,
            'owner': self
        })

        self._ui_list_name = f'ZENU_UL_AUTOGEN_{self.name}_list'

        lst = type(self._ui_list_name, (ZENU_UL_base_list,),
                   {'custom_draw': self._draw})

        self._op = actions
        self._ui_list = lst

        self._reg, self._unreg = bpy.utils.register_classes_factory((
            actions,
            lst,
            self._property_group
        ))

    def _draw(self, layout: bpy.types.UILayout, item: Any):
        pass

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, new_index: int):
        length = len(self.prop_list)

        if new_index <= 0:
            new_index = 0
        if new_index >= length:
            new_index = length - 1

        self._index = new_index

    @property
    def prop_list(self) -> list[T]:
        return getattr(bpy.context.scene, self._property_list_name)

    def remove(self, index: int):
        self.prop_list.remove(index)
        self.index = index

    def add(self) -> T:
        item = self.prop_list.add()
        self.index = self.index

        return item

    def check_index(self, new_index: int):
        length = len(self.prop_list)

        if new_index <= 0:
            new_index = 0
        if new_index >= length:
            new_index = length - 1

        return new_index

    def move(self, index: int, new_index: int):
        new_index = self.check_index(new_index)
        self.prop_list.move(index, new_index)
        self.index = new_index

    @property
    def active(self) -> T:
        if len(self.prop_list) <= 0:
            return None

        return self.prop_list[self.index]

    @property
    def prev_active(self) -> T:
        if self._prev_active is None:
            return self.active

        try:
            return self.prop_list[self._prev_active]
        except IndexError:
            return None

    def draw_op(self, layout: bpy.types.UILayout, action: str, icon: str):
        op = layout.operator(self._op_idname, text='', icon=icon)
        op.action = action

    def _on_select(self):
        pass

    def draw_ui(self, layout: bpy.types.UILayout):
        scene = bpy.context.scene
        row = layout.row()

        row.template_list(self._ui_list_name, '',
                          scene, self._property_list_name,
                          scene, self._active_prop_name)

        col_main = row.column()

        col = col_main.column(align=True)
        self.draw_op(layout=col, action='ADD', icon='ADD')
        self.draw_op(layout=col, action='REMOVE', icon='REMOVE')

        col = col_main.column(align=True)
        self.draw_op(layout=col, action='UP', icon='TRIA_UP')
        self.draw_op(layout=col, action='DOWN', icon='TRIA_DOWN')

    def _setter(self, scene, value: int):
        self._prev_active = self.index
        self.index = value
        return None

    def _getter(self, scene):
        return self._index

    def unregister(self):
        self._unreg()

    def register(self):
        self._reg()

        setattr(self._active_path, self._active_prop_name,
                bpy.props.IntProperty(update=lambda s, f: self._on_select(),
                                      get=lambda scene: self._getter(scene),
                                      set=lambda scene, value: self._setter(
                                          scene, value)
                                      ))
        setattr(self._active_path, self._property_list_name,
                bpy.props.CollectionProperty(type=self._property_group))

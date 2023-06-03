from ..context_group import ContextGroup
from . import menu_overlays, menu_actions, menu_modifiers

overlays = ContextGroup(name='Overlays')
overlays.register_classes(menu_overlays.classes)

properties = ContextGroup(name='Actions')
properties.register_classes(menu_actions.classes)

modifiers = ContextGroup(name='Modifiers')
modifiers.register_classes(menu_modifiers.classes)



classes = (
    properties,
    overlays,
    modifiers
)
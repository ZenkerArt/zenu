from .node_category import NodeCategory

general = NodeCategory('General')
character_equip = NodeCategory('Character Equipment')
dialog = NodeCategory('Dialog')
animation = NodeCategory('Animation')



def register():
    general.register()
    character_equip.register()
    dialog.register()
    animation.register()


def unregister():
    general.unregister()
    character_equip.unregister()
    animation.unregister()

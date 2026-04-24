from .node_category import NodeCategory

general = NodeCategory('General')
character_equip = NodeCategory('Character Equipment')



def register():
    general.register()
    character_equip.register()


def unregister():
    general.unregister()
    character_equip.unregister()

from .menu_group import MenuGroup, OperatorItem


class MenuManager:
    up: MenuGroup
    left: MenuGroup
    right: MenuGroup
    down: MenuGroup

    def __init__(self):
        self.clear()

    def clear(self):
        self.up = MenuGroup()
        self.down = MenuGroup()
        self.left = MenuGroup()
        self.right = MenuGroup()


menu_3d_view = MenuManager()
menu_timeline = MenuManager()

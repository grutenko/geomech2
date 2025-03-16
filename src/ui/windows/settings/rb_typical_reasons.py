import wx

from src.database import RBTypicalPreventAction

from .entity_list import EntityList


class RbTypicalReasons(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, RBTypicalPreventAction)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

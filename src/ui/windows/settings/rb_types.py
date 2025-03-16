import wx

from src.database import RBType

from .entity_list import EntityList


class RbTypes(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, RBType)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

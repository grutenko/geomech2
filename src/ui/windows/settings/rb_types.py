import wx

from src.database import RBType

from .entity_list import EntityList


class RbTypes(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, RBType)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

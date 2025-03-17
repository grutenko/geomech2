import wx

from src.database import PmProperty

from .entity_list import EntityList


class PmProperties(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, PmProperty)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

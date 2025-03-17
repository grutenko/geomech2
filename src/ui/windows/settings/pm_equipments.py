import wx

from src.database import PmTestEquipment

from .entity_list import EntityList


class PmEquipments(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, PmTestEquipment)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

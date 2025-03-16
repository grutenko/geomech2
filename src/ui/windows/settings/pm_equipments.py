import wx

from src.database import PmTestEquipment

from .entity_list import EntityList


class PmEquipments(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, PmTestEquipment)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

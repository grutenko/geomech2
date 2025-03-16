import wx

from src.database import PmPerformedTask

from .entity_list import EntityList


class PmTasks(EntityList):
    def __init__(self, parent):
        super().__init__(parent, {}, PmPerformedTask)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

import wx

from src.database import PmPerformedTask

from .entity_list import EntityList


class PmTasks(EntityList):
    def __init__(self, parent):
        columns = {"Name": ("Название", lambda: ..., 250), "Comment": ("Комментарий", lambda: ..., 350)}
        super().__init__(parent, columns, PmPerformedTask)
        self.Hide()

    def start(self):
        self.Show()

    def end(self):
        self.Hide()

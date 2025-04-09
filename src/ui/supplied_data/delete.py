from pony.orm import db_session, rollback

from src.database import SuppliedData, SuppliedDataPart
from src.ui.task import TaskJob


class DeleteTask(TaskJob):
    def __init__(self, entities):
        self.entities = entities
        super().__init__()

    @db_session
    def run(self):
        self.set_progress(0, len(self.entities))
        for index, o in enumerate(self.entities):
            if self.cancel_event.isSet():
                rollback()
                return
            if isinstance(o, SuppliedData):
                _o = SuppliedData[o.RID]
            elif isinstance(o, SuppliedDataPart):
                _o = SuppliedDataPart[o.RID]
            else:
                rollback()
                raise RuntimeError("Unexpected object type: %s" % str(type(o)))
            _o.delete()
            self.set_progress(index + 1, len(self.entities))

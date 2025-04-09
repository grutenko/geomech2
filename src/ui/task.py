import threading
from typing import Protocol, runtime_checkable

import wx


@runtime_checkable
class TaskJob(Protocol):
    progress = -1
    total = -1
    message = None
    cancel_event = None
    lock = None

    def __init__(self):
        self.progress = -1
        self.total = -1
        self.message = None
        self.cancel_event = threading.Event()
        self.lock = threading.Lock()

    def set_progress(self, progress=-1, total=-1, message=None):
        with self.lock:
            self.progress = progress
            self.total = total
            self.message = message

    def run(self):
        """
        Запускает задачу в работу. Метод должен вернуть результат работы.
        При желании можно менять прогресс используя self.set_progress(progress, total, message)
        Также в задаче можно использовать self.cancel_event.is_set() для проерки не была ли отменена
        задача пользователем
        """
        ...


class Task(wx.ProgressDialog):
    def __init__(self, title, message, job: TaskJob, parent=None, can_abort=True, show_time=True):
        style = wx.PD_AUTO_HIDE
        if can_abort:
            style |= wx.PD_CAN_ABORT
        if show_time:
            style |= wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME
        if not isinstance(job, TaskJob):
            raise RuntimeError("invalid task job.")
        super().__init__(title, message, style=style, parent=parent)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_alarm)
        self.job = job

        self.status = "alive"
        self._e = None
        self._ret = None
        self._on_resolve = lambda *args, **kwds: ...

        def on_reject(e):
            raise e

        self._on_reject = on_reject
        self._is_cancel = False

    def is_cancel(self):
        return self._is_cancel

    def on_alarm(self, event):
        with self.job.lock:
            if self.status == "alive":
                if self.job.message is not None:
                    self.Update(self.gauge.GetValue(), self.job.message)
                if self.job.progress == -1:
                    self.Pulse()
                else:
                    self.SetRange(self.job.total)
                    self.Update(self.job.progress)
                if self.WasCancelled():
                    self.job.cancel_event.set()
                    self._is_cancel = True
                return

        self.timer.Stop()
        self.SetRange(1)
        self.Update(1)
        self.Close()
        if self.status == "resolve":
            self._on_resolve(self._ret)
        elif self.status == "reject":
            self._on_reject(self._e)
        self.Destroy()

    def then(self, on_resolve, on_reject):
        self._on_resolve = on_resolve
        self._on_reject = on_reject

    def run(self):
        def task(job):
            ret = None
            try:
                ret = job.run()
            except Exception as e:
                with self.job.lock:
                    self.status = "reject"
                    self._e = e
            else:
                with self.job.lock:
                    self.status = "resolve"
                    self._ret = ret

        self.thread = threading.Thread(target=task, args=(self.job,))
        self.thread.start()
        self.timer.Start(100)

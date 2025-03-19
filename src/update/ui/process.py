import tempfile
import threading

import wx

from ..update import download_update


def sizeof_human(v):
    m = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    _i = 0
    while v > 1024:
        v /= 1024
        _i += 1
    return "{:.3f} {}".format(v, m[_i])


class UpdateProcess(wx.Dialog):
    def __init__(self, parent, url: str, appname: str):
        self.url = url
        self.appname = appname
        self.dest = None
        self.thread = None
        self.exception = None
        self.is_cancel = False
        super().__init__(parent, title="Обновление", style=wx.DEFAULT_DIALOG_STYLE & ~(wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX) | wx.STAY_ON_TOP)
        self.CenterOnScreen()
        sz = wx.BoxSizer(wx.VERTICAL)
        sz_in = wx.BoxSizer(wx.VERTICAL)
        self.text = wx.StaticText(self, label="Идет скачивание обновления.")
        sz_in.Add(self.text, 0, wx.EXPAND)
        sz_in_h = wx.BoxSizer(wx.HORIZONTAL)
        self.gauge = wx.Gauge(self, size=wx.Size(250, -1))
        sz_in_h.Add(self.gauge, 0, wx.EXPAND)
        self.cancel_btn = wx.Button(self, label="Отменить")
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        sz_in_h.Add(self.cancel_btn, 0, wx.EXPAND | wx.LEFT, border=5)
        sz_in.Add(sz_in_h, 0, wx.EXPAND)
        sz.Add(sz_in, 1, wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()
        self.Fit()

    def on_cancel(self, event):
        self.is_cancel = True

    def start(self):
        file = tempfile.NamedTemporaryFile(delete=False)
        file.close()
        self.dest = file.name

        def task(url, appname, dest):
            try:
                for progress, total in download_update(url, appname, dest):
                    if self.is_cancel:
                        break
                    wx.CallAfter(self.gauge.SetRange, total)
                    wx.CallAfter(self.gauge.SetValue, progress)
                    wx.CallAfter(self.text.SetLabelText, "Идет скачиваение обновления... (%s / %s)" % (sizeof_human(progress), sizeof_human(total)))
            except Exception as e:
                self.exception = e
            finally:
                self.EndModal(wx.ID_OK)

        self.thread = threading.Thread(target=task, args=(self.url, self.appname, self.dest))
        self.thread.start()

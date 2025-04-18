from dataclasses import dataclass

import wx

from src.config import Config


class MainWindowStub(wx.Frame):
    def open(self, code: str, **kwds) -> None: ...
    def close(self, wnd: wx.Panel) -> None: ...


@dataclass
class AppCtx:
    datadir: str = None
    config: Config = None
    config_filename: str = None
    config_is_fallback_runtime: bool = False
    main: MainWindowStub = None


__ctx__: AppCtx = AppCtx()


def app_ctx() -> AppCtx:
    global __ctx__
    return __ctx__

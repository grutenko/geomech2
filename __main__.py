import logging
import os
import sys
import traceback

import wx
from pony.orm import Database, DBException, db_session

import src.database
from src.config import Config
from src.ctx import app_ctx
from src.ui.windows.login import LoginDialog
from src.ui.windows.main import MainWindow

# Сообщаем PyInstaller, что загрузка завершена
if os.getenv("_PYI_SPLASH_IPC"):
    try:
        from pyi_splash import close  # type: ignore

        close()
    except:
        ...


if __name__ == "__main__":
    app = wx.App(False, useBestVisual=True)

    def show_exception(e: Exception):
        message = "Uncaught exception:\n"
        message += "".join(traceback.format_exception(e.__class__, e, e.__traceback__))
        logging.exception(message)

        dlg = wx.MessageDialog(None, "Ошибка: " + str(e), str(e.__class__), wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def excepthook(exception_type, exception_value, exception_traceback):
        show_exception(exception_value)

    sys.excepthook = excepthook

    if "GEOMECH_CONFDIR" in os.environ:
        datadir = os.environ["GEOMECH_CONFDIR"]
    else:
        datadir = "~/.geomech"
    datadir = os.path.expanduser(os.path.expandvars(datadir))

    if not os.path.exists(datadir):
        os.mkdir(datadir)
    logging.basicConfig(
        filename=datadir + "/app.log",  # Файл для записи логов
        level=logging.ERROR,  # Уровень логирования, чтобы записывать только ошибки
        format="%(asctime)s - %(levelname)s - %(message)s",  # Формат записи
    )

    try:
        cfg = Config.from_file("%s/config.json" % datadir, create=True)
    except OSError as e:
        wx.MessageBox(str(e), "Ошибка конфигурации")
        cfg = Config.runtime()
    app_ctx().config = cfg
    _connection_failed = True
    if cfg.login is not None and cfg.password is not None and cfg.database is not None and cfg.host is not None and cfg.port is not None:
        try:
            db = Database()
            db.bind(provider="postgres", user=cfg.login, password=cfg.password, host=cfg.host, port=cfg.port, database=cfg.database)
            with db_session:
                db.execute('SELECT * FROM "DischargeMeasurements" LIMIT 1')
        except DBException as e:
            logging.exception(str(e))
        else:
            _connection_failed = False

    _start_accept = False
    if _connection_failed:
        dlg = LoginDialog()
        if dlg.ShowModal() == wx.ID_OK:
            _start_accept = True
    else:
        _start_accept = True
    if _start_accept:
        cfg = app_ctx().config
        src.database.connect(login=cfg.login, password=cfg.password, host=cfg.host, port=cfg.port, database=cfg.database)
        wnd = MainWindow()
        app_ctx().main = wnd
        app.SetTopWindow(wnd)
        app.MainLoop()

import wx
from pony.orm import Database

from src.config import flush
from src.ctx import app_ctx
from src.ui.icon import get_icon
from src.ui.validators import TextValidator


class LoginDialog(wx.Dialog):
    def __init__(self, parent=None, mode="LOGIN", without_config=False):
        super().__init__(None, title="База данных геомеханики")
        self.SetIcon(wx.Icon(get_icon("logo")))
        self.SetSize(270, 230)
        self.login = None
        self.password = None
        self.database = None
        self.host = None
        self.port = None
        self.without_config = without_config
        sz = wx.BoxSizer(wx.VERTICAL)
        main_sz = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, label="логин:")
        main_sz.Add(label, 0, wx.EXPAND)
        self.field_login = wx.TextCtrl(self, size=wx.Size(250, 20))
        self.field_login.SetValidator(TextValidator(lenMin=1, lenMax=32))
        main_sz.Add(self.field_login, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(self, label="пароль:")
        main_sz.Add(label, 0, wx.EXPAND)
        self.field_password = wx.TextCtrl(self, size=wx.Size(250, 20), style=wx.TE_PASSWORD)
        self.field_password.SetValidator(TextValidator(lenMin=1, lenMax=32))
        main_sz.Add(self.field_password, 0, wx.EXPAND | wx.BOTTOM, border=10)
        sz.Add(main_sz, 1, wx.EXPAND | wx.ALL, border=10)
        self.colpane = wx.CollapsiblePane(self, label="Параметры подключения")
        p = self.colpane.GetPane()
        p_sz = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(p, label="база данных:")
        p_sz.Add(label, 0, wx.EXPAND)
        self.field_database = wx.TextCtrl(p, size=wx.Size(250, 20))
        self.field_database.SetValidator(TextValidator(lenMin=1, lenMax=32))
        p_sz.Add(self.field_database, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(p, label="хост:")
        p_sz.Add(label, 0, wx.EXPAND)
        self.field_host = wx.TextCtrl(p, size=wx.Size(250, 20))
        self.field_host.SetValidator(TextValidator(lenMin=1, lenMax=32))
        p_sz.Add(self.field_host, 0, wx.EXPAND | wx.BOTTOM, border=10)
        label = wx.StaticText(p, label="порт:")
        p_sz.Add(label, 0, wx.EXPAND)
        self.field_port = wx.SpinCtrl(p, size=wx.Size(250, 20), min=0, max=65535)
        p_sz.Add(self.field_port, 0, wx.EXPAND | wx.BOTTOM, border=10)
        p.SetSizer(p_sz)
        main_sz.Add(self.colpane, 0, wx.GROW | wx.BOTTOM, border=10)
        hr = wx.StaticLine(self)
        sz.Add(hr, 0, wx.EXPAND)
        btn_sz = wx.StdDialogButtonSizer()
        if mode == "LOGIN":
            _name = "Войти"
        else:
            _name = "Изменить доступы"
        self.btn_login = wx.Button(self, label=_name)
        btn_sz.Add(self.btn_login, 0)
        sz.Add(btn_sz, 0, wx.ALIGN_RIGHT | wx.ALL, border=10)
        self.SetSizer(sz)
        self.Layout()
        self.CenterOnScreen()
        if not self.without_config:
            self.paste_credentials_from_config()
        else:
            self.paste_credentials_default()
        self.btn_login.Bind(wx.EVT_BUTTON, self.on_login)

    def paste_credentials_default(self):
        self.field_login.SetValue("postgres")
        self.field_password.SetValue("postgres")
        self.field_database.SetValue("geomech")
        self.field_host.SetValue("127.0.0.1")
        self.field_port.SetValue(5432)

    def paste_credentials_from_config(self):
        cfg = app_ctx().config
        if "login" in cfg:
            self.field_login.SetValue(cfg.login)
        if "password" in cfg:
            self.field_password.SetValue(cfg.password)
        if "database" in cfg:
            self.field_database.SetValue(cfg.database)
        else:
            self.field_database.SetValue("geomech")
        if "host" in cfg:
            self.field_host.SetValue(cfg.host)
        else:
            self.field_host.SetValue("192.168.1.7")
        if "port" in cfg:
            self.field_port.SetValue(cfg.port)
        else:
            self.field_port.SetValue(5432)

    def on_login(self, event):
        if not self.Validate():
            return
        login = self.field_login.GetValue()
        password = self.field_password.GetValue()
        database = self.field_database.GetValue()
        host = self.field_host.GetValue()
        port = self.field_port.GetValue()
        try:
            db = Database()
            db.bind(provider="postgres", user=login, password=password, database=database, host=host, port=port)
        except Exception as e:
            wx.MessageBox(str(e), "Ошибка подключения к базе данных", style=wx.OK | wx.ICON_ERROR)
        else:
            if not self.without_config:
                cfg = app_ctx().config
                cfg.login = login
                cfg.password = password
                cfg.database = database
                cfg.host = host
                cfg.port = port
                flush(cfg, app_ctx().config_filename)
            else:
                self.login = login
                self.password = password
                self.database = database
                self.host = host
                self.port = port
            self.EndModal(wx.ID_OK)

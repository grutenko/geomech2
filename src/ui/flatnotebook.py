import wx
import wx.lib.agw.flatnotebook


class xFlatNotebook(wx.lib.agw.flatnotebook.FlatNotebook):
    def __init__(self, *args, **kwargs):
        kwargs["agwStyle"] |= wx.lib.agw.flatnotebook.FNB_RIBBON_TABS
        super().__init__(*args, **kwargs)
        self.disabled_tabs = set()
        self.Bind(wx.lib.agw.flatnotebook.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.on_page_changing)

    def on_page_changing(self, event):
        new_selection = event.GetSelection()
        if new_selection in self.disabled_tabs:
            wx.Bell()  # Звук при попытке перейти
            event.Veto()  # Отменяем переключение
        else:
            event.Skip()

    def enable_tab(self, tabindex, enable=True):
        if enable:
            if tabindex in self.disabled_tabs:
                page = self.GetPage(tabindex)
                if page is not None:
                    page.Enable()
                    self.SetPageTextColour(tabindex, wx.Colour(0, 0, 0))
                self.disabled_tabs.remove(tabindex)
        else:
            page = self.GetPage(tabindex)
            if page is not None:
                page.Disable()
                self.SetPageTextColour(tabindex, wx.Colour(150, 150, 150))
            self.disabled_tabs.add(tabindex)

import wx
from pony.orm import commit, db_session
from pubsub import pub


@db_session
def delete_object(o, relations=[]) -> bool:
    dlg = wx.MessageDialog(
        None, "Вы действительно хотите удалить объект: %s?\nЭто действие необратимо." % o.Name, "Подтвердите удаление", wx.YES | wx.NO | wx.NO_DEFAULT | wx.ICON_ASTERISK
    )
    if dlg.ShowModal() != wx.ID_YES:
        return False

    def _show_error():
        wx.MessageBox("Запрещено удалять объекты к которым есть связаные данные.", "Удаление запрещено", wx.OK | wx.CENTRE | wx.ICON_ERROR)

    o = type(o)[o.RID]
    for relation in relations:
        if len(getattr(o, relation)) > 0:
            _show_error()
            return False

    o.delete()
    commit()
    pub.sendMessage("object.deleted", o=o)
    return True

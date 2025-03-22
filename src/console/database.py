##
## Локальная sqlite база данных с локальными скриптами для консоли
##

from pony.orm import Database, Optional, Required, Set

from src.ctx import app_ctx

db = Database()


def connect():
    global db
    db.bind(provider="sqlite", filename=app_ctx().datadir + "/console.dbsqlite", create_db=True)
    db.generate_mapping(create_tables=True)


class Folder(db.Entity):
    _table_ = "folder"

    name = Required(str)
    parent = Optional("Folder")
    folders = Set("Folder")
    files = Set("File")


class File(db.Entity):
    _table_ = "file"

    name = Required(str, unique=True)
    content = Required(str)
    folder = Optional(Folder)

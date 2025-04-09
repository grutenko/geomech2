import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from typing import List

from pony.orm import db_session

from src.database import SuppliedDataPart
from src.ui.task import TaskJob

# Таске нужно передавать относительный путь до создаваемого обьекта
# Если обьект является потомком другого объекта, то он должен родительский обьект должен стоять перед дочерним
# Пример:
# Папка 1:
# ---> Файл 1
# ---> Файл 2
# items = [
#     DownloadItem("Папка 1"),
#     DownloadItem("Папка 1/Файл 1.pdf", SuppliedDataPart[1]),
#     DownloadItem("Папка 1/Файл 2.pdf", SuppliedDataPart[2]),
# ]
# В целом планируется генерировать пути из названий, но это уже работа того класса который будет
#  создавать эту таску. с.м. SuppliedDataWidget.on_download()


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*\n\r\t]', "_", filename).strip(" .")


@dataclass
class DownloadItem:
    path: str
    # Для файлов передаем SuppliedDataPart для получаения DataContent
    # Для папок можно просто редавать относителный путь
    o: SuppliedDataPart | None = None


class DownloadTask(TaskJob):
    def __init__(self, items: List[DownloadItem], dest: str):
        self.items = items
        self.dest = dest
        super().__init__()

    @db_session
    def run(self):
        with tempfile.TemporaryDirectory() as dir:
            for index, item in enumerate(self.items):
                path = os.path.join(dir, item.path)
                if item.o is None:
                    os.mkdir(path)
                else:
                    with open(path, "wb") as file:
                        file.write(SuppliedDataPart[item.o.RID].DataContent)
                self.set_progress(index + 1, len(self.items), path)
            for item in os.listdir(dir):
                shutil.move(os.path.join(dir, item), self.dest)

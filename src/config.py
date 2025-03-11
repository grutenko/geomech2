import json
import os
import shutil

import attrdict2


class Config(attrdict2.AttrDict):
    @classmethod
    def runtime(cls):
        return cls({}, use_runtime=True)

    @classmethod
    def from_file(cls, filepath, create: bool = False):
        """
        Метод для загрузки конфигурации из файла.
        Поддерживает форматы JSON, можно расширить для других форматов.
        """
        if not os.path.exists(filepath) and create:
            with open(filepath, "w+") as f:
                f.write("{}")
        data = {}
        with open(filepath, "r") as file:
            data = json.load(file)  # Здесь можно использовать другие форматы, например YAML
        return cls(data, filename=filepath)

    def __init__(self, data, filename: str = None, use_runtime: bool = False):
        self.__filename = filename
        self.__use_runtime = use_runtime
        super().__init__(data)

    def flush(self):
        if self.__use_runtime:
            return
        _tmp_filename = self.__filename + ".tmp"
        f = open(_tmp_filename, "w")
        try:
            f.write(json.dumps(self, indent=4))
            f.close()
        except Exception:
            raise
        else:
            shutil.copyfile(_tmp_filename, self.__filename)
        finally:
            f.close()
            os.remove(_tmp_filename)


class ClassConfigProvider:
    def __init__(self, config: Config, classname: str):
        self._cfg = config
        self._classname = classname

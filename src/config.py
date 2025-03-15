import json
import os
import shutil

import attrdict2


class Config(attrdict2.AttrDict):
    @classmethod
    def runtime(cls):
        return cls({})

    def __getattr__(self, key):
        return self.get(key, None)

    def __init__(self, data):
        super().__init__(data)


def load_from_file(filename: str, create: bool = False):
    if not os.path.exists(filename) and create:
        with open(filename, "w+") as f:
            f.write("{}")
    data = {}
    with open(filename, "r") as file:
        data = json.load(file)  # Здесь можно использовать другие форматы, например YAML
    return Config(data)


def flush(config: Config, filename: str):
    _tmp_filename = filename + ".tmp"
    f = open(_tmp_filename, "w")
    try:
        f.write(json.dumps(config, indent=4))
        f.close()
    except Exception:
        raise
    else:
        shutil.copyfile(_tmp_filename, filename)
    finally:
        f.close()
        os.remove(_tmp_filename)


class ClassConfigProvider:
    def __init__(self, config: Config, classname: str):
        self._cfg = config
        self._classname = classname

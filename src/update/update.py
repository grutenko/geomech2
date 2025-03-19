import logging
from typing import Iterator, Tuple

import requests


def check_update_available(url: str, appname: str, ver: str) -> bool:
    """
    Проверяет наличие обновлений
    """
    try:
        response = requests.get("%s/%s-latest-version.txt" % (url, appname), timeout=1)
        version = response.content.decode()
        ver0 = ver.split(".")
        ver1 = version.split(".")
        for _i, component in enumerate(ver0):
            if int(component) < int(ver1[_i]):
                return True
            elif int(component) > int(ver1[_i]):
                return False
    except Exception as e:
        logging.exception(str(e))
        return False
    return False


def download_update(url: str, appname: str, dest: str) -> Iterator[Tuple[int, int]]:
    """
    Скачивает обновление в файл dest
    """
    response = requests.get("%s%s-latest.exe" % (url, appname), stream=True, timeout=1)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 4096
    file = open(dest, "wb")
    left = 0
    try:
        for data in response.iter_content(block_size):
            left += len(data)
            file.write(data)
            yield (left, total_size)
    except Exception:
        raise
    finally:
        file.close()


def download_checksum(url: str, appname: str) -> str:
    """
    Скачивает контрольную сумму
    """
    data = None
    try:
        response = requests.get("%s/%s-latest.sha256" % (url, appname), timeout=1)
    except Exception as e:
        logging.exception(str(e))
    return True


def check(filename: str, checksum: str) -> bool:
    """
    Проверяет файл на соответствие контрольной сумме
    """
    ...


def run_switch_version_script(filename: str, target_exe_filename: str):
    """
    Запускает на выполнние скрипт смены версий. Он будет дожидаться завершения основной
    программы после чего заменит текущий исполняемый файл новым обновлением.
    """
    ...

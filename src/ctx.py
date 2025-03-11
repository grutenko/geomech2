from dataclasses import dataclass
from src.config import Config
import src.ui.windows.main


@dataclass
class AppCtx:
    config: Config = None
    main: src.ui.windows.main.MainWindow = None


__ctx__: AppCtx = AppCtx()


def app_ctx() -> AppCtx:
    global __ctx__
    return __ctx__

from dataclasses import dataclass

from src.config import Config


@dataclass
class AppCtx:
    config: Config = None
    main: object = None


__ctx__: AppCtx = AppCtx()


def app_ctx() -> AppCtx:
    global __ctx__
    return __ctx__

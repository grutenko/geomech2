from dataclasses import dataclass

from src.config import Config


@dataclass
class AppCtx:
    config: Config = None
    config_filename: str = None
    config_is_fallback_runtime: bool = False
    main: object = None


__ctx__: AppCtx = AppCtx()


def app_ctx() -> AppCtx:
    global __ctx__
    return __ctx__

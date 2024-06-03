import enum
import os
from pathlib import Path
from typing import Optional, Set, cast

from pydantic_settings import BaseSettings, SettingsConfigDict


class Exchange(str, enum.Enum):
    okx = "okx"
    binance = "binance"


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
    )

    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    okx_api_key: Optional[str] = None
    okx_api_secret: Optional[str] = None
    exchange: Exchange
    timeframe: str
    limit: int
    smpt_port: Optional[int] = None
    smpt_password: Optional[str] = None
    smpt_user: Optional[str] = None
    smpt_server: Optional[str] = None
    tg_token: Optional[str] = None
    filters: Set[str]

    @property
    def user_data_dir(self) -> Path:
        return Path(os.environ["USER_DATA_DIR"])


class LazySettings:
    _settings: Optional[_Settings] = None

    def load(self, settings: _Settings) -> None:
        self._settings = settings

    def __str__(self) -> str:
        return str(self._settings)

    def __repr__(self) -> str:
        return repr(self._settings)

    def __getattr__(self, name: str):
        if self._settings is None:
            raise RuntimeError("Settings not initialized")
        return getattr(self._settings, name)


settings = cast(_Settings, LazySettings())


def load_filter():
    """从用户配置目录中加载过滤器"""

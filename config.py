"""Application configuration."""
from __future__ import annotations

import os

BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    APP_NAME: str = 'MVP Cuba 2011'
    DB_PATH: str = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'torneo.db'))
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
    # Cache static files (logos, banners, sprites) for 1 week.
    # Kills the per-nav revalidation flicker on team logos.
    SEND_FILE_MAX_AGE_DEFAULT: int = 60 * 60 * 24 * 7


class DevConfig(BaseConfig):
    DEBUG: bool = True


class ProdConfig(BaseConfig):
    DEBUG: bool = False


configs: dict[str, type[BaseConfig]] = {
    'dev': DevConfig,
    'prod': ProdConfig,
    'default': DevConfig,
}

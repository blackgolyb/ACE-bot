from functools import lru_cache
from pathlib import Path
import typing

from envparse import Env
from pydantic import (
    Field,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_FOLDER = Path(__file__).parent.parent.parent
ENV_FOLDER = PROJECT_FOLDER / "env"
MODULES_MODULE = "src.modules"


def get_model_config(**kwargs: typing.Unpack[SettingsConfigDict]) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        **kwargs,
    )


class Bot(BaseSettings):
    token: str
    attempts: int
    attempt_sleep: int
    admins: list[int]


class Core(BaseSettings):
    project_folder: Path = PROJECT_FOLDER
    debug: bool = True


class Database(BaseSettings):
    url: str


class Config(BaseSettings):
    core: Core = Field(default_factory=Core)
    db: Database
    bot: Bot

    model_config = get_model_config()


def load_env_by_env_type(
    env: Env,
    env_type: str | None,
    env_folder: Path,
    /,
    is_scrict: bool = False,
) -> None:
    env_file_name = ".env"
    if env_type:
        env_file_name = f".env.{env_type.lower()}"

    env_file = env_folder / env_file_name

    if env_file.exists():
        env.read_envfile(env_file)
    elif is_scrict:
        raise FileNotFoundError(f"Environment file not found: {env_file}")


@lru_cache
def get_config() -> Config:
    env = Env()
    env_type = env.str("ENV_TYPE", default="dev")

    load_env_by_env_type(env, env_type, ENV_FOLDER)

    return Config()

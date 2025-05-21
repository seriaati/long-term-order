from __future__ import annotations

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    discord_token: str
    db_url: str

    shioaji_api_key: str
    shioaji_api_secret: str

    ca_path: str
    ca_password: str
    ca_person_id: str

    simulation: bool = True


load_dotenv()
CONFIG = Config()  # pyright: ignore[reportCallIssue]

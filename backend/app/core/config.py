from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Workflow Hub API"
    api_v1_prefix: str = "/api/v1"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60 * 24
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "workflow_user"
    mysql_password: str = "workflow_password"
    mysql_database: str = "workflow_hub"
    frontend_origins: str = "http://localhost:5173"
    upload_dir: str = "uploads"
    auto_init_db: bool = True
    auto_seed_db: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="WORKFLOW_",
    )

    @cached_property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @cached_property
    def frontend_origin_list(self) -> list[str]:
        return [item.strip() for item in self.frontend_origins.split(",") if item.strip()]

    @cached_property
    def upload_path(self) -> Path:
        project_root = Path(__file__).resolve().parents[2]
        return project_root / self.upload_dir


settings = Settings()

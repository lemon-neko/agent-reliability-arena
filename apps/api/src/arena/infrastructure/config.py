"""Environment-backed configuration with conservative local defaults."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    arena_env: str = "development"
    arena_host: str = "127.0.0.1"
    arena_port: int = 8000
    database_url: str = "sqlite:///runtime/arena.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    celery_task_always_eager: bool = True
    model_base_url: str = "fake://deterministic"
    model_api_key: str = ""
    model_name: str = "fake-deterministic"
    allow_external_models: bool = False
    scenario_dir: Path = Field(
        default_factory=lambda: REPOSITORY_ROOT / "packages" / "scenarios" / "catalog"
    )
    risk_pack_dir: Path = Field(
        default_factory=lambda: REPOSITORY_ROOT
        / "packages"
        / "risk-packs"
        / "tool-agent-baseline"
        / "v1"
    )
    registry_dir: Path = Field(default_factory=lambda: REPOSITORY_ROOT / "packages" / "registry")
    runtime_dir: Path = Field(default_factory=lambda: REPOSITORY_ROOT / "runtime")

    @property
    def is_demo(self) -> bool:
        return self.arena_env == "demo"


settings = Settings()

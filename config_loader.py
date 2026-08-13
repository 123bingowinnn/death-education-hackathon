from __future__ import annotations

import os
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    import tomli as tomllib
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


@dataclass(frozen=True)
class Settings:
    amap_api_key: str
    amap_endpoint: str
    kimi_api_key: str
    kimi_model: str
    kimi_endpoint: str
    default_city: str
    recommendation_cache_seconds: int

    @property
    def amap_ready(self) -> bool:
        return bool(self.amap_api_key)

    @property
    def kimi_ready(self) -> bool:
        return bool(self.kimi_api_key)


def load_settings() -> Settings:
    _load_dotenv(BASE_DIR / ".env")
    config = _load_toml(BASE_DIR / "config.toml")
    llm = config.get("llm", {})
    amap = config.get("amap", {})
    app = config.get("app", {})

    return Settings(
        amap_api_key=os.getenv("AMAP_API_KEY", str(amap.get("api_key", ""))),
        amap_endpoint=os.getenv(
            "AMAP_ENDPOINT", str(amap.get("endpoint", "https://restapi.amap.com"))
        ).rstrip("/"),
        kimi_api_key=os.getenv("KIMI_API_KEY", str(llm.get("api_key", ""))),
        kimi_model=os.getenv("KIMI_MODEL", str(llm.get("model", "kimi-k2.6"))),
        kimi_endpoint=os.getenv(
            "KIMI_ENDPOINT", str(llm.get("endpoint", "https://api.moonshot.cn/v1"))
        ).rstrip("/"),
        default_city=os.getenv("DEFAULT_CITY", str(app.get("default_city", "北京"))),
        recommendation_cache_seconds=int(
            os.getenv(
                "RECOMMENDATION_CACHE_SECONDS",
                str(app.get("recommendation_cache_seconds", 1800)),
            )
        ),
    )


settings = load_settings()

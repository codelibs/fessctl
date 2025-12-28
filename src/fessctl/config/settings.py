from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class Settings:
    fess_endpoint: str = field(default_factory=lambda: os.getenv(
        "FESS_ENDPOINT", "http://localhost:8080"))
    access_token: str | None = field(
        default_factory=lambda: os.getenv("FESS_ACCESS_TOKEN", None))
    fess_version: str = field(
        default_factory=lambda: os.getenv("FESS_VERSION", "15.4.0"))

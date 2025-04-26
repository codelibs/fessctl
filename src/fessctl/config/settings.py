from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    fess_endpoint: str = os.getenv("FESS_ENDPOINT", "http://localhost:8080")
    access_token: str = os.getenv("FESS_ACCESS_TOKEN")


settings = Settings()

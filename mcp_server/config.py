import os
from dataclasses import dataclass


@dataclass
class Settings:
    API_BASE_URL: str = os.getenv("ARCLAT_API_URL", "https://api.arclat.com")
    API_KEY: str = os.getenv("ARCLAT_API_KEY", "")


settings = Settings()

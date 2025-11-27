import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Bot configuration from environment variables"""
    telegram_token: str
    openrouter_api_key: str
    data_file: str = "data/data.txt"

    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def validate(self):
        """Validate that all required fields are present"""
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env")

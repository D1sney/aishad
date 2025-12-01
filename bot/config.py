import os
import json
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.json"


@dataclass
class RAGConfig:
    """RAG configuration"""
    chunk_size: int = 400
    top_k: int = 5
    embedding_model: str = "all-MiniLM-L6-v2"


@dataclass
class AdminConfig:
    """Admin configuration"""
    user_ids: List[int] = None

    def __post_init__(self):
        if self.user_ids is None:
            self.user_ids = []


@dataclass
class BotConfig:
    """Bot configuration from environment variables and config.json"""
    telegram_token: str
    openrouter_api_key: str
    data_file: str = "data/data.txt"
    rag: RAGConfig = None
    admin: AdminConfig = None

    def __post_init__(self):
        if self.rag is None:
            self.rag = RAGConfig()
        if self.admin is None:
            self.admin = AdminConfig()

    @classmethod
    def from_env(cls):
        """Create config from environment variables and config.json"""
        # Load from .env
        bot_config = cls(
            telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        # Load from config.json
        bot_config.load_json_config()
        return bot_config

    def load_json_config(self):
        """Load configuration from config.json"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Load RAG config
                if 'rag' in data:
                    self.rag = RAGConfig(**data['rag'])

                # Load Admin config
                if 'admin' in data:
                    self.admin = AdminConfig(**data['admin'])

    def save_json_config(self):
        """Save current configuration to config.json"""
        data = {
            "rag": {
                "chunk_size": self.rag.chunk_size,
                "top_k": self.rag.top_k,
                "embedding_model": self.rag.embedding_model
            },
            "admin": {
                "user_ids": self.admin.user_ids
            }
        }

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def validate(self):
        """Validate that all required fields are present"""
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env")

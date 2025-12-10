import logging
from pathlib import Path
from typing import List, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API using a plain system prompt with full data.txt"""

    def __init__(self, api_key: str, model: str = "amazon/nova-2-lite-v1:free", data_file: str = "data/data.txt"):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key
            model: Model name to use
            data_file: Path to full knowledge base text that will be injected into the system prompt
        """
        self.model = model
        self.data_file = Path(data_file)
        self.knowledge_base_text = self._load_data()
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        logger.info(f"OpenRouter client initialized with model: {model}")

    def _load_data(self) -> str:
        """Load the full knowledge base from disk"""
        try:
            text = self.data_file.read_text(encoding="utf-8")
            logger.info(f"Loaded knowledge base from {self.data_file} ({len(text)} chars)")
            return text
        except FileNotFoundError:
            logger.error(f"Knowledge base file not found: {self.data_file}")
            return ""
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            return ""

    def generate_answer(self, query: str) -> str:
        """
        Generate answer using the entire knowledge base injected into the system prompt

        Args:
            query: User question

        Returns:
            Generated answer
        """
        logger.info(f"Generating answer for query: {query}")

        system_prompt = f"""Ты помощник для абитуриентов Школы анализа данных (ШАД).
Отвечай на вопросы только на основе предоставленного контекста базы знаний.
Если в базе знаний нет нужной информации, честно скажи об этом.

Формат ответа (Markdown, совместимая с Telegram):
- коротко и по делу; максимум 5–7 пунктов
- тон дружелюбный, поддерживающий, как умный добрый помощник
- можно использовать *жирный* и _курсив_
- списки через "-"
- добавляй уместные эмодзи, но не перегружай (0–2 на весь ответ)
- не используй заголовки (###), таблицы, ссылки и кодовые блоки
- никаких дополнительных комментариев

Полный контекст базы знаний:
{self.knowledge_base_text}"""

        user_message = f"Вопрос: {query}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                extra_body={"reasoning": {"enabled": True}}
            )

            answer = response.choices[0].message.content
            logger.info(f"Generated answer: {answer[:200]}...")
            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Извините, произошла ошибка при генерации ответа. Попробуйте позже."

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Chat with model (for future use)

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Model response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                extra_body={"reasoning": {"enabled": True}}
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "Извините, произошла ошибка."

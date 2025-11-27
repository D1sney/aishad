import logging
from openai import OpenAI
from typing import List, Dict

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API using Grok model"""

    def __init__(self, api_key: str, model: str = "x-ai/grok-4.1-fast:free"):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key
            model: Model name to use
        """
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        logger.info(f"OpenRouter client initialized with model: {model}")

    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using RAG context

        Args:
            query: User question
            context: Retrieved context from RAG

        Returns:
            Generated answer
        """
        logger.info(f"Generating answer for query: {query}")
        logger.info(f"Retrieved context:\n{context[:500]}...")  # Log first 500 chars

        system_prompt = """Ты помощник для абитуриентов Школы анализа данных (ШАД).
Отвечай на вопросы на основе предоставленного контекста.
Используй только ту информацию, которая есть в контексте.
Отвечай кратко, четко и по делу на русском языке."""

        user_message = f"""Контекст из базы знаний:
{context}

Вопрос: {query}

Дай ответ на основе контекста выше."""

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

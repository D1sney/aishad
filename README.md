# ШАД Admission Bot

Telegram-бот для помощи абитуриентам Школы анализа данных (ШАД), использующий RAG (Retrieval-Augmented Generation) для ответов на вопросы.

## Технологии

- **aiogram 3** - Telegram Bot API
- **sentence-transformers** - локальные embeddings
- **FAISS** - векторный поиск
- **OpenRouter** - доступ к Grok LLM
- **Python 3.8+**

## Структура проекта

```
aishad/
├── bot/                      # Telegram bot
│   ├── config.py            # Конфигурация
│   ├── handlers.py          # Обработчики сообщений
│   └── logger_config.py     # Настройка логирования
├── rag/                      # RAG система
│   ├── embeddings.py        # Создание embeddings
│   └── retriever.py         # Поиск релевантных фрагментов
├── llm/                      # LLM клиент
│   └── openrouter_client.py # OpenRouter API
├── data/
│   └── data.txt             # База знаний о ШАД
├── main.py                   # Точка входа
└── requirements.txt
```

## Установка

1. Клонируйте репозиторий и перейдите в папку:
```bash
cd aishad
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Создайте файл `.env` на основе `.env.example`:
```bash
copy .env.example .env
```

6. Заполните `.env` своими ключами:
```
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
OPENROUTER_API_KEY=ваш_ключ_от_OpenRouter
```

## Настройка данных

Отредактируйте файл `data/data.txt` и добавьте информацию о ШАД:
- Программы обучения
- Требования для поступления
- Процесс поступления
- FAQ
- Контакты

Бот автоматически разобьет текст на части и создаст векторный индекс при запуске.

## Запуск

```bash
python main.py
```

При первом запуске бот загрузит модель embeddings (~90MB), это может занять несколько минут.

## Использование

1. Найдите бота в Telegram по username
2. Отправьте `/start`
3. Задавайте вопросы о поступлении в ШАД

Бот будет:
1. Искать релевантные фрагменты из базы знаний
2. Отправлять их вместе с вопросом в Grok
3. Возвращать сгенерированный ответ

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Справка по использованию

## Логирование

Логи сохраняются в:
- Консоль (stdout)
- Файл `bot.log`

Уровень логирования: INFO

## Разработка

### Изменение модели embeddings

В файле `rag/embeddings.py` измените параметр `model_name`:
```python
EmbeddingModel(model_name='другая-модель')
```

### Изменение LLM модели

В файле `llm/openrouter_client.py` измените параметр `model`:
```python
OpenRouterClient(api_key=key, model="другая/модель")
```

### Настройка RAG

В файле `rag/retriever.py`:
- `chunk_size` - размер фрагментов текста (по умолчанию 300)
- `top_k` - количество извлекаемых фрагментов (по умолчанию 3)

## Troubleshooting

**Ошибка: TELEGRAM_BOT_TOKEN not set**
- Проверьте файл `.env`
- Убедитесь, что файл находится в корне проекта

**Бот не отвечает**
- Проверьте логи в `bot.log`
- Убедитесь, что API ключи корректны
- Проверьте подключение к интернету

**Медленные ответы**
- Это нормально для бесплатной модели Grok
- Рассмотрите использование платной модели

## Лицензия

MIT

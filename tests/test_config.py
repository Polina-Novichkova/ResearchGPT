
from core.config import (
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    TAVILY_API_KEY,
    DATABASE_URL
)

print("Конфигурация загружена!")
print("LLM_PROVIDER:", LLM_PROVIDER)
print("OLLAMA_BASE_URL:", OLLAMA_BASE_URL)
print("OLLAMA_MODEL:", OLLAMA_MODEL)
print("TAVILY_API_KEY:", "указан" if TAVILY_API_KEY else "не указан")
print("DATABASE_URL:", "указан" if DATABASE_URL else "не указан")

import os

from dotenv import load_dotenv

load_dotenv()

#Настройки языковой модели
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

#Настройки Ollama
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434/v1"
)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

# Настройки поиска
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Настройки PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

import ollama
from core.config import OLLAMA_MODEL

def get_llm_client():
    return ollama.Client(
        host="http://localhost:11434"
    )

def get_model_name() -> str:
    return OLLAMA_MODEL

def generate_response(prompt: str) -> str:
    #Отправка запроса локальной модели и возвращание её ответа
    client = get_llm_client()

    response = client.chat(
        model=get_model_name(),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


import ollama
from core.config import OLLAMA_MODEL

def get_llm_client():
    return ollama.Client(
        host="http://localhost:11434"
    )

def get_model_name() -> str:
    return OLLAMA_MODEL


def generate_response(prompt: str) -> str:
    client = get_llm_client()

    print("Отправляем запрос в Ollama...")

    response = client.chat(
        model=get_model_name(),
        messages=[
            {"role": "user", "content": prompt}
        ],
        think=False,
        format="json",
        options={
            "num_predict": 4000,
            "repeat_penalty": 1.1,
            "repeat_last_n": 128
        }
    )

    print("Ответ от Ollama получен!")

    return response["message"]["content"]

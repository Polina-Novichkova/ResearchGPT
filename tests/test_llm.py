from services.llm import generate_response, get_model_name

def main():
    print("Подключение к Ollama...")
    print("Используемая модель:", get_model_name())

    response = generate_response(
        "Привет! Объясни, какую задачу решает наш проект ResearchGPT."
    )

    print("\nОтвет Qwen 3 4B:")
    print(response)

if __name__ == "__main__":
    main()


import ollama
def main():
    client = ollama.Client(
    host="http://localhost:11434"
)
    #Отправка запроса локальной модели
    response = client.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "user",
                "content": "Привет! Объясни, что такое мультиагентная система."
            }
        ]
    )

    print("\nОтвет локальной модели:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()

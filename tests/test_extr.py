
from agents.extraction_agent import extract_from_url, extract_main_text, clean_text


def test_nasa_article():
    url = "https://www.nasa.gov/centers-and-facilities/johnson/chapea-mission-2-crew-reflects-after-378-days-on-simulated-mars/"

    document = extract_from_url(url)

    assert document is not None, "Не удалось извлечь статью NASA"
    assert document["title"], "Отсутствует заголовок"
    assert document["source"], "Отсутствует источник"
    assert document["content"], "Отсутствует текст статьи"
    assert len(document["content"]) >= 100, "Текст слишком короткий"

    print("Тест NASA пройден!")
    print("Заголовок:", document["title"])
    print("Источник:", document["source"])
    print("Количество символов:", len(document["content"]))
    print("Количество абзацев:", len(document["content"].split("\n\n")))


def test_short_text():
    html = """
    <!DOCTYPE html>
    <html>
        <head><title>Test page</title></head>
        <body>
            <nav>Navigation</nav>
            <footer>Footer</footer>
        </body>
    </html>
    """

    result = extract_main_text(html)

    assert result is not None, "Trafilatura не вернула результат"

    content = result.get("text")

    if not content:
        print("Тест короткого текста пройден!")
        return

    content = clean_text(content)

    assert len(content) < 100, "Тестовый текст неожиданно оказался длинным"

    print("Тест короткого текста пройден!")
    print("Количество символов:", len(content))


def main():
    print("\n========== ТЕСТ 1: NASA ==========\n")
    test_nasa_article()

    print("\n========== ТЕСТ 2: КОРОТКИЙ ТЕКСТ ==========\n")
    test_short_text()

    print("\nВсе тесты завершены!")


if __name__ == "__main__":
    main()

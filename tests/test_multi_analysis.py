from agents.extraction_agent import extract_from_url
from agents.analysis_agent import run_analysis_agent


URLS = [
    "https://www.nasa.gov/centers-and-facilities/johnson/chapea-mission-2-crew-reflects-after-378-days-on-simulated-mars/",

    "https://www.nasa.gov/missions/analog-field-testing/chapea/first-mars-crew-completes-yearlong-simulated-red-planet-nasa-mission/",

    "https://www.nasa.gov/humans-in-space/chapea/about-chapea/"
]

SUBQUESTION = (
    "Каковы цели программы CHAPEA, как проходят симуляции "
    "марсианских миссий и какие результаты они дают?"
)


def main():
    documents = []

    print("\n========== ИЗВЛЕЧЕНИЕ СТАТЕЙ ==========")

    for url in URLS:
        print(f"\nОбрабатываем: {url}")

        try:
            document = extract_from_url(url)

            if document:
                documents.append(document)
                print("Статья успешно извлечена.")
            else:
                print("Не удалось извлечь статью.")

        except Exception as error:
            print(f"Ошибка извлечения: {error}")

    print("\nКоличество извлечённых статей:", len(documents))

    if not documents:
        raise RuntimeError(
            "Не удалось извлечь ни одной статьи."
        )

    print("\n========== МУЛЬТИАНАЛИЗ ==========")

    result = run_analysis_agent(
        documents,
        SUBQUESTION
    )

    print("\n========== РЕЗУЛЬТАТЫ ==========")

    print("\nОбщий статус:", result.relevance_status)

    print("\nКоличество summary:", len(result.summaries))

    print("\nКлючевые тезисы:")
    for point in result.key_points:
        print("-", point)

    print("\nФакты:")
    for fact in result.facts:
        print("-", fact.statement)
        print("  Evidence:", fact.evidence)
        print("  Контекст:", fact.event_context)
        print("  Источник:", fact.source_url)

    print("\nЧисловые данные:")
    for number in result.numbers:
        print("-", number.value)
        print("  Описание:", number.description)
        print("  Источник:", number.source_url)

    print("\nГруппы фактов:")
    for group in result.fact_groups:
        print("-", group.statement)
        print("  Количество фактов:", len(group.facts))
        print("  Контекст:", group.event_context)
        print("  Источники:", group.source_urls)

    print("\nИсточники:")
    for url in result.source_urls:
        print("-", url)

    print("\n========== ПРОВЕРКИ ==========")

    assert result.relevance_status in {
        "relevant",
        "partially_relevant",
        "not_relevant",
        "analysis_failed",
        "no_sources"
    }

    assert all(
        fact.source_url in [doc["url"] for doc in documents]
        for fact in result.facts
    )

    assert all(
        number.source_url in [doc["url"] for doc in documents]
        for number in result.numbers
    )

    for group in result.fact_groups:
        assert len(group.facts) > 1

        for fact in group.facts:
            assert fact.event_context == group.event_context

    print("Проверки структуры и источников пройдены.")


if __name__ == "__main__":
    main()

import time
from agents.search_agent import run_search_agent
from agents.planner import create_research_plan
from services.search_service import search_multiple_queries

def main():
    questions = [
        "Искусственный интеллект в образовании",
        "Преимущества ИИ в обучении",
        "Риски использования ИИ",
        "Будущее ИИ в образовании"
    ]
    start = time.perf_counter()
    res = search_multiple_queries(questions, max_queries=2)
    end = time.perf_counter()
    print("Количество найденных источников:", len(res))
    print(f"Время поиска: {end - start:.2f} секунд")
    
if __name__ == "__main__":
    main()
    
    
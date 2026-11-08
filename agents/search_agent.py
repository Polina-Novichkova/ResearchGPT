from services.search_service import search_multiple_queries

def run_search_agent(topic: str, subquestions: list[str]):
    queries = [topic] + subquestions
    res = search_multiple_queries(queries)
    return res
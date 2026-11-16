import time
from tavily import TavilyClient
from core.config import TAVILY_API_KEY
from concurrent.futures import ThreadPoolExecutor
from services.url_utils import normalize_url

def get_search_client():
    return TavilyClient(api_key = TAVILY_API_KEY)

def search_web(query: str, max_res: int = 5) -> dict | None:
    for attempt in range(3):
        try:
            client = get_search_client()
            response = client.search(
                query = query,
                max_results = max_res,
                timeout = 30
            )
            return response
        except Exception as error: 
            print(f'Попытка {attempt + 1} не удалась: {error}')
            if attempt < 2:
                time.sleep(2)
    return None
    
def remove_duplicates(results):
    unique_res = []
    seen_urls = set()
    
    for res in results:
        url = res.get('url', '').strip()
        
        if not url:
            continue
        
        normalized_url = normalize_url(url)
        
        if not normalized_url or normalized_url in seen_urls:
            continue
        
        unique_res.append(res)
        seen_urls.add(normalized_url)
            
    return unique_res

def search_multiple_queries(subquestions: list[str], max_queries: int = 5) -> list[dict]:
    all_res = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        responses = executor.map(search_web, subquestions[:max_queries])
        for response in responses:
            if response is None:
                continue
            response = response['results']
            all_res.extend(response)
    all_res = remove_duplicates(all_res)
    return all_res
import requests
import trafilatura
import json
import urllib.robotparser
from urllib.parse import urlparse

def check_robots(url: str):
    parsed = urlparse(url)
    robots_url = f'{parsed.scheme}://{parsed.netloc}/robots.txt'
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as error:
        print(f'Ошибка при чтении robots.txt: {error}')
        return False
    return rp.can_fetch('*', url)

def get_page_html(url: str):
    if not check_robots(url):
        print('Загрузка страницы запрещена правилами robots.txt')
        return None
    try:
        response = requests.get(url, timeout = 30)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
            print('Данный ресурс не является HTML-страницей')
            return None
        return response.text
    
    except requests.exceptions.Timeout:
        print(f"Превышено время ожидания ответа от сервера")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Не удалось установить соединение с сервером")
        return None
    except requests.exceptions.HTTPError as error:
        print(f"Ошибка HTTP: {error}")
        return None
    except requests.exceptions.RequestException as error:
        print(f"Ошибка при получении страницы: {error}")
        return None

def extract_main_text(html: str):
    res = trafilatura.extract(
        html, 
        output_format = "json",
        with_metadata = True
    )
    if res is None or not res:
        return None
    data = json.loads(res)
    return data

def clean_text(text: str):
    paragr = text.split("\n")
    seen = set()
    clean_paragr = []
    for i in paragr:
        clean = " ".join(i.split())
        clean_t = "".join(char for char in clean if char.isprintable())
        if clean_t not in seen and clean_t:
            seen.add(clean_t)
            clean_paragr.append(clean_t)
    clean_paragr = "\n\n".join(clean_paragr)
    return clean_paragr 
    
def extract_from_url(url: str):
    html = get_page_html(url)
    if html is None:
        return None
    result = extract_main_text(html)
    if result is None:
        return None
    parsed = urlparse(url)
    title = result.get('title')
    content = result.get('text')
    
    published_date = result.get('date')
    source = result.get('hostname') or parsed.netloc
    author = result.get('author')
    if not content: 
        return None
    content = clean_text(content)
    
    if not content or len(content) < 100:
        return None
        
    document = {
        'title': title,
        'url': url,
        'source': source,
        'published_date': published_date,
        'author': author,
        'content': content
    }
    
    return document     
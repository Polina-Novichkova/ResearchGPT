from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
from agents.analysis_agent import FactGroup
import re

MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
@lru_cache(maxsize = 1)
def get_embedding_model():
    model = SentenceTransformer(MODEL_NAME)
    return model

def generate_embeddings(texts: list[str]):
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings

def calculate_all_similarities(embeddings):
    similarities = cosine_similarity(embeddings)
    return similarities

def find_similar_pairs(embeddings, threshold = 0.9):
    similarities = calculate_all_similarities(embeddings)
    pairs = []
    for i in range(len(similarities)):
        for j in range(i + 1, len(similarities)):
            if similarities[i][j] >= threshold:
                pairs.append((i, j, similarities[i][j]))
    return pairs

def find_similar_facts(facts, threshold = 0.9):
    if len(facts) < 2:
        return []
    statements = [fact.statement for fact in facts]
    embeddings = generate_embeddings(statements)
    
    pairs = find_similar_pairs(embeddings, threshold)
    
    res = []
    for i, j, similarity in pairs:
        res.append({
            'fact_1': facts[i],
            'fact_2': facts[j],
            'similarity': float(similarity)
        })
    return res

def extract_numbers(text: str):
    pattern = r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:[.,]\d+)?'
    numbers = re.findall(pattern, text)
    
    normalized_numbers = []
    for number in numbers:
        if re.fullmatch(r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?', number):
            normalized_number = number.replace(',', '')
        else:
            normalized_number = number.replace(',', '.')
        value = float(normalized_number)
        if value.is_integer():
            value = int(value)
        normalized_numbers.append(value)
    return normalized_numbers

def have_same_numbers(text_1: str, text_2: str) -> bool:
    numbers_1 = extract_numbers(text_1)
    numbers_2 = extract_numbers(text_2)
    return numbers_1 == numbers_2

UNIT_ALIASES = {
    # Время
    'day': 'day',
    'days': 'day',
    'день': 'day',
    'дня': 'day',
    'дней': 'day',

    'week': 'week',
    'weeks': 'week',

    'month': 'month',
    'months': 'month',
    'месяц': 'month',
    'месяца': 'month',
    'месяцев': 'month',

    'year': 'year',
    'years': 'year',
    'год': 'year',
    'года': 'year',
    'лет': 'year',

    'hour': 'hour',
    'hours': 'hour',
    'час': 'hour',
    'часа': 'hour',
    'часов': 'hour',

    'minute': 'minute',
    'minutes': 'minute',
    'минута': 'minute',
    'минуты': 'minute',
    'минут': 'minute',

    'second': 'second',
    'seconds': 'second',
    'секунда': 'second',
    'секунды': 'second',
    'секунд': 'second',

    # Расстояние
    'kilometer': 'kilometer',
    'kilometers': 'kilometer',
    'meter': 'meter',
    'meters': 'meter',
    'mile': 'mile',
    'miles': 'mile',

    # Масса
    'kilogram': 'kilogram',
    'kilograms': 'kilogram',
    'gram': 'gram',
    'grams': 'gram',

    # Площадь
    'square foot': 'square_foot',
    'square feet': 'square_foot',
    'square meter': 'square_meter',
    'square meters': 'square_meter',
    'square kilometer': 'square_kilometer',
    'square kilometers': 'square_kilometer',

    # Длина и углы
    'foot': 'foot',
    'feet': 'foot',
    'inch': 'inch',
    'inches': 'inch',
    'degree': 'degree',
    'degrees': 'degree',

    # Количество людей
    'person': 'person',
    'people': 'person',
    'persons': 'person',
    'человек': 'person',

    # Проценты
    '%': 'percent',
    'percent': 'percent',
    'percents': 'percent',

    # Валюта
    'рубль': 'ruble',
    'рубля': 'ruble',
    'рублей': 'ruble',
    'доллар': 'dollar',
    'доллара': 'dollar',
    'долларов': 'dollar'
}


UNIT_PATTERN = re.compile(
    r'-?\d+(?:[.,]\d+)?\s*'
    r'(?P<unit>'
    r'square\s+(?:feet|foot|meters?|kilometers?)|'
    r'percent(?:s)?|'
    r'kilometers?|meters?|miles?|'
    r'kilograms?|grams?|'
    r'weeks?|days?|months?|years?|'
    r'hours?|minutes?|seconds?|'
    r'inches|inch|feet|foot|degrees?|'
    r'people|persons?|person|'
    r'рублей|рубля|рубль|'
    r'долларов|доллара|доллар|'
    r'человек|'
    r'года|лет|год|'
    r'месяцев|месяца|месяц|'
    r'дней|день|дня|'
    r'часов|часа|час|'
    r'минут|минута|минуты|'
    r'секунд|секунда|секунды|'
    r'%'
    r')(?!\w)',
    re.IGNORECASE
)

def extract_units(text: str):

    units = []
    for match in UNIT_PATTERN.finditer(text):
        unit = match.group('unit').lower()
        normalized_unit = UNIT_ALIASES.get(unit, unit)
        units.append(normalized_unit)
    return units

def have_same_units(text_1: str, text_2: str) -> bool:
    units_1 = extract_units(text_1)
    units_2 = extract_units(text_2)
    
    return units_1 == units_2

def have_same_event_context(context_1: str, context_2: str) -> bool:
    context_1 = " ".join(context_1.lower().split())
    context_2 = " ".join(context_2.lower().split())
    
    if not context_1 or not context_2:
        return False
    return context_1 == context_2

def compare_facts(fact_1, fact_2, threshold = 0.9):
    statements = [fact_1.statement, fact_2.statement]
    
    embeddings = generate_embeddings(statements)
    similarity = cosine_similarity(embeddings)[0][1]
    
    numbers_1 = extract_numbers(fact_1.statement)
    numbers_2 = extract_numbers(fact_2.statement)

    same_numbers = numbers_1 == numbers_2

    numbers_compatible = (
        same_numbers if numbers_1 or numbers_2 else True
    )

    units_1 = extract_units(fact_1.statement)
    units_2 = extract_units(fact_2.statement)

    same_units = units_1 == units_2

    units_compatible = (
        same_units if units_1 or units_2 else True
    )

    same_event = have_same_event_context(
        fact_1.event_context,
        fact_2.event_context
    )

    is_similar = (
        similarity >= threshold
        and numbers_compatible
        and units_compatible
        and same_event
    )

    return {
        'similarity': float(similarity),
        'same_numbers': same_numbers,
        'same_units': same_units,
        'same_event': same_event,
        'numbers_compatible': numbers_compatible,
        'units_compatible': units_compatible,
        'is_similar': bool(is_similar)
    }
    
def find_dupl_cand(facts, threshold = 0.9):
    duplicates = []
    
    for i in range(len(facts)):
        for j in range(i + 1, len(facts)):
            comparison = compare_facts(facts[i], facts[j], threshold)
            if comparison['is_similar']:
                duplicates.append({
                    'fact_1': facts[i],
                    'fact_2': facts[j],
                    'similarity': comparison['similarity']
                })
    return duplicates

def group_dupl_facts(facts, threshold = 0.9):
    groups = []
    
    for fact in facts:
        target_group = None

        for group in groups:
            is_dupl_of_all = True
            for f in group:
                comparison = compare_facts(
                    fact,
                    f,
                    threshold
                )
                
                if not (comparison['is_similar']):
                    is_dupl_of_all = False
                    break
            if is_dupl_of_all:
                target_group = group
                break
            
        if target_group is not None:
            target_group.append(fact)
        else:
            groups.append([fact])

    return [group for group in groups if(len(group) > 1)]

def create_fact_groups(facts, threshold = 0.9):
    duplicate_groups = group_dupl_facts(facts, threshold)
    fact_groups = []
    
    for group in duplicate_groups:
        source_urls = []
        for fact in group:
            url = fact.source_url.strip()
            if url and url not in source_urls:
                source_urls.append(url)
        
        fact_group = FactGroup(
            statement = group[0].statement,
            facts = group,
            source_urls = source_urls,
            event_context = group[0].event_context
        )
        
        fact_groups.append(fact_group)
    return fact_groups
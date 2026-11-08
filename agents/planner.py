from pydantic import BaseModel, Field, field_validator, model_validator
from services.llm import generate_response

class ResearchPlan(BaseModel):
    topic: str
    subquestions: list[str] = Field(
        min_length = 3,
        max_length = 5
    )

    #Проверка корректности вопросов
    @field_validator('subquestions')
    @classmethod
    def validate_subquestions(cls, questions):
        clean_qua = []
        unique_qua = set()
        for q in questions:
            clean_q = q.strip()
            if not clean_q:
                raise ValueError('Вопрос не может быть пустым')
            if clean_q.lower() in unique_qua:
                raise ValueError('Вопросы не могут повторяться')
            unique_qua.add(clean_q.lower())
            clean_qua.append(clean_q)
        return clean_qua

class PlanValidation(BaseModel):
    is_valid: bool
    issues: list[str]
    corrected_subquestions: list[str] = Field(
        default_factory = list,
        max_length = 5
    )
    
    @model_validator(mode = 'after')
    def validate_result(self):
        if self.is_valid:
            if self.issues or self.corrected_subquestions:
                raise ValueError('У корректного плана не должно быть проблем и исправлений')
        else:
            if not self.issues:
                raise ValueError('Необходимо указать обнаруженные проблемы')
            if not 3 <= len(self.corrected_subquestions) <= 5:
                raise ValueError('Необходимо предоставить от 3 до 5 исправленных вопросов')
        return self
    
def create_planner_prompt(topic: str) -> str:
    prompt = f"""
    Задача: проанализировать переданную тему
    Разбей тему на 3-5 самостоятельных исследовательских вопросов
    Количество подвопросов должно составлять от 3 до 5
    Каждый вопрос должен раскрывать отдельный аспект исходной темы
    Подвопрос не должен быть перефразированием исходной темы
    Не нужно создавать вопросы, которые спрашивают только определение исходной темы
    Вопросы должны быть достаточно конкретными для самостоятельного поиска информации в Интернете
    Вопросы должны охватывать тему с разных сторон
    Не повторяй исходную тему другими словами
    Не создавай повторяющиеся вопросы
    Возвращай результат в формате JSON с двумя полями:
    - topic (исходная тема)
    - subquestions (список подвопросов)
    Верни только корректный JSON без Markdown-разметки и дополнительных пояснений
    Тема исследования: {topic}
    """
    return prompt

def generate_research_plan(topic: str):
    prompt = create_planner_prompt(topic)
    response = generate_response(prompt)
    return ResearchPlan.model_validate_json(response)

def create_validation_prompt(topic: str, subquestions: list[str]) -> str:
    prompt = f"""
    Проверь план исследования
    
    Тема: {topic}
    Вопросы: {subquestions}

    Критерии проверки:
    1. Вопросы раскрывают разные аспекты темы
    2. Нет смысловых повторов
    3. Вопросы достаточно конкретны для поиска информации
    4. Вопросы не повторяют исходную тему

    Если все вопросы корректны:
    - is_valid = true
    - issues = []
    - corrected_subquestions = []

    Если есть проблемы:
    - is_valid = false
    - issues = список обнаруженных проблем
    - corrected_subquestions = исправленный список вопросов
    Сохрани от 3 до 5 вопросов
    Не изменяй корректные вопросы

    Верни только JSON:
    {{
        "is_valid": true,
        "issues": [],
        "corrected_subquestions": []
    }}
    """
    return prompt
    
 
def validate_research_plan(topic: str, subquestions: list[str]) -> PlanValidation:
    prompt = create_validation_prompt(topic, subquestions)
    response = generate_response(prompt)  
    return PlanValidation.model_validate_json(response)

def create_research_plan(topic: str) -> ResearchPlan:
    plan = generate_research_plan(topic)
    validation = validate_research_plan(
        plan.topic,
        plan.subquestions
    )
    if validation.is_valid:
        return plan
    return ResearchPlan(
        topic = plan.topic,
        subquestions = validation.corrected_subquestions
    )
if __name__ == "__main__":
    plan = generate_research_plan("Искусственный интеллект в образовании")
    print(plan)

    validation = validate_research_plan(
        plan.topic,
        plan.subquestions
    )
    print(validation)

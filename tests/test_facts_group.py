from agents.analysis_agent import Fact, FactGroup

fact_1 = Fact(
    statement='Компания увеличила выручку на 20%',
    evidence='Выручка выросла на 20 процентов.',
    source_url='https://source1.com'
)

fact_2 = Fact(
    statement='Выручка организации выросла на 20%',
    evidence='Организация сообщила о росте выручки на 20%.',
    source_url='https://source2.com'
)

group = FactGroup(
    statement='Компания увеличила выручку на 20%',
    facts=[fact_1, fact_2],
    source_urls=[
        fact_1.source_url,
        fact_2.source_url
    ]
)

print('\n========== ГРУППА ФАКТОВ ==========')

print('Общее утверждение:', group.statement)
print('Количество фактов:', len(group.facts))
print('Источники:', group.source_urls)

for fact in group.facts:
    print('\nФакт:', fact.statement)
    print('Доказательство:', fact.evidence)
    print('Источник:', fact.source_url)
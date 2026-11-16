
import pytest

from agents import verification_agent as va


def make_fact():
    return va.Fact(
        statement='Компания открыла завод в Италии в 2025 году',
        evidence='Компания открыла новый завод',
        source_url='https://original.com/article',
        event_context='Открытие завода'
    )


def make_evidence(
    source_url='https://source.com/article',
    supports_claim=True,
    evidence='Компания открыла завод в Италии',
    statement='Компания открыла завод в Италии'
):
    return va.VerificationEvidence(
        statement=statement,
        evidence=evidence,
        source_url=source_url,
        supports_claim=supports_claim
    )


def make_result(evidence=None):
    return va.VerificationResult(
        original_statement='Компания открыла завод в Италии',
        status='unverified',
        explanation='Проверка утверждения',
        evidence=evidence or []
    )


# --------------------------------------------------
# URL UTILS
# --------------------------------------------------

def test_get_domain():
    assert va.get_domain('https://www.example.com/page') == 'example.com'


def test_normalize_url():
    first = va.normalize_url(
        'HTTPS://WWW.Example.com/article/?b=2&a=1#section'
    )
    second = va.normalize_url(
        'https://example.com/article?a=1&b=2'
    )

    assert first == second


def test_normalize_invalid_url():
    assert va.normalize_url('invalid-url') == ''


# --------------------------------------------------
# FIND VERIFICATION SOURCES
# --------------------------------------------------

def test_find_verification_sources_filters_duplicates(monkeypatch):
    fact = make_fact()

    search_results = [
        {
            'url': 'https://original.com/another',
            'title': 'Original source',
            'content': 'Original content',
            'score': 1.0
        },
        {
            'url': 'https://other.com/article',
            'title': 'Independent article',
            'content': 'A' * 250,
            'score': 0.9
        },
        {
            'url': 'https://www.other.com/article/',
            'title': 'Another article',
            'content': 'B' * 250,
            'score': 0.8
        },
        {
            'url': 'https://third.com/article',
            'title': 'Third article',
            'content': 'C' * 250,
            'score': 0.7
        }
    ]

    monkeypatch.setattr(
        va,
        'generate_verification_query',
        lambda fact: 'test query'
    )

    monkeypatch.setattr(
        va,
        'search_multiple_queries',
        lambda queries, max_queries: search_results
    )

    result = va.find_verification_sources(fact)

    assert len(result) == 2
    assert result[0]['url'] == 'https://other.com/article'
    assert result[1]['url'] == 'https://third.com/article'


def test_find_verification_sources_empty_query(monkeypatch):
    monkeypatch.setattr(
        va,
        'generate_verification_query',
        lambda fact: ''
    )

    result = va.find_verification_sources(make_fact())

    assert result == []


# --------------------------------------------------
# EXTRACT VERIFICATION DOCUMENTS
# --------------------------------------------------

def test_extract_documents_removes_duplicate_redirect_urls(monkeypatch):
    sources = [
        {'url': 'https://site.com/first'},
        {'url': 'https://site.com/second'}
    ]

    def fake_extract(url):
        return {
            'url': 'https://site.com/final',
            'content': 'A' * 250
            if url.endswith('first')
            else 'B' * 250
        }

    monkeypatch.setattr(va, 'extract_from_url', fake_extract)

    result = va.extract_verification_documents(sources)

    assert len(result) == 1


def test_extract_documents_skips_invalid_normalized_url(monkeypatch):
    sources = [
        {'url': 'http://example.com:bad/path'}
    ]

    monkeypatch.setattr(
        va,
        'extract_from_url',
        lambda url: {
            'url': 'http://example.com:bad/path',
            'content': 'Some document content'
        }
    )

    result = va.extract_verification_documents(sources)

    assert result == []


def test_extract_documents_skips_extraction_errors(monkeypatch):
    sources = [
        {'url': 'https://site.com/article'}
    ]

    def fake_extract(url):
        raise ConnectionError('Connection failed')

    monkeypatch.setattr(va, 'extract_from_url', fake_extract)

    result = va.extract_verification_documents(sources)

    assert result == []


# --------------------------------------------------
# VALIDATE VERIFICATION EVIDENCE
# --------------------------------------------------

def test_validate_evidence_removes_invalid_and_duplicate_quotes():
    valid = make_evidence()
    duplicate = make_evidence()

    invalid_quote = make_evidence(
        evidence='Цитаты нет в документе'
    )

    original_source = make_evidence(
        source_url='https://original.com/article'
    )

    result = make_result([
        valid,
        duplicate,
        invalid_quote,
        original_source
    ])

    documents = [
        {
            'url': 'https://source.com/article',
            'content': 'Компания открыла завод в Италии'
        }
    ]

    va.validate_verification_evidence(
        result,
        documents,
        'https://original.com/article'
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].evidence == 'Компания открыла завод в Италии'


# --------------------------------------------------
# VALIDATE EVIDENCE RELEVANCE
# --------------------------------------------------

def test_validate_relevance_keeps_supporting_evidence(monkeypatch):
    result = make_result([make_evidence()])

    response = (
        '{"relation": "supports", '
        '"explanation": "Цитата подтверждает открытие завода"}'
    )

    monkeypatch.setattr(
        va,
        'generate_response',
        lambda prompt: response
    )

    va.validate_evidence_relevance(result, make_fact())

    assert len(result.evidence) == 1
    assert result.evidence[0].supports_claim is True
    assert result.evidence[0].explanation == (
        'Цитата подтверждает открытие завода'
    )


def test_validate_relevance_removes_irrelevant_evidence(monkeypatch):
    result = make_result([make_evidence()])

    response = (
        '{"relation": "irrelevant", '
        '"explanation": "Цитата не относится к утверждению"}'
    )

    monkeypatch.setattr(
        va,
        'generate_response',
        lambda prompt: response
    )

    va.validate_evidence_relevance(result, make_fact())

    assert result.evidence == []


def test_validate_relevance_skips_llm_errors(monkeypatch):
    result = make_result([make_evidence()])

    def fake_generate_response(prompt):
        raise RuntimeError('Ollama unavailable')

    monkeypatch.setattr(
        va,
        'generate_response',
        fake_generate_response
    )

    va.validate_evidence_relevance(result, make_fact())

    assert result.evidence == []


# --------------------------------------------------
# SYNCHRONIZE VERIFICATION STATUS
# --------------------------------------------------

@pytest.mark.parametrize(
    'evidence, expected_status',
    [
        (
            [
                make_evidence('https://one.com'),
                make_evidence('https://two.com')
            ],
            'verified'
        ),
        (
            [make_evidence('https://one.com')],
            'partially_verified'
        ),
        (
            [
                make_evidence(
                    'https://one.com',
                    supports_claim=False
                )
            ],
            'contradicted'
        ),
        (
            [
                make_evidence('https://one.com'),
                make_evidence(
                    'https://two.com',
                    supports_claim=False
                )
            ],
            'partially_verified'
        ),
        (
            [],
            'unverified'
        )
    ]
)
def test_synchronize_verification_status(evidence, expected_status):
    result = make_result(evidence)

    va.synchronize_verification_status(result)

    assert result.status == expected_status


def test_synchronize_sources_are_unique():
    result = make_result([
        make_evidence('https://one.com'),
        make_evidence('https://one.com'),
        make_evidence('https://two.com')
    ])

    va.synchronize_verification_status(result)

    assert result.supporting_sources == [
        'https://one.com',
        'https://two.com'
    ]


# --------------------------------------------------
# VERIFY FACT
# --------------------------------------------------

def test_verify_fact_without_documents():
    result = va.verify_fact(make_fact(), [])

    assert result.status == 'insufficient_sources'
    assert result.evidence == []


def test_verify_fact_with_valid_evidence(monkeypatch):
    fact = make_fact()

    documents = [
        {
            'url': 'https://source.com/article',
            'title': 'Independent article',
            'content': 'Компания открыла завод в Италии'
        }
    ]

    verification_response = (
        '{'
        '"original_statement": "Компания открыла завод в Италии",'
        '"status": "verified",'
        '"explanation": "Утверждение подтверждено",'
        '"evidence": [{'
        '"statement": "Компания открыла завод в Италии",'
        '"evidence": "Компания открыла завод в Италии",'
        '"source_url": "https://source.com/article",'
        '"supports_claim": true'
        '}]'
        '}'
    )

    relevance_response = (
        '{"relation": "supports", '
        '"explanation": "Цитата подтверждает утверждение"}'
    )

    responses = iter([
        verification_response,
        relevance_response
    ])

    monkeypatch.setattr(
        va,
        'generate_response',
        lambda prompt: next(responses)
    )

    result = va.verify_fact(fact, documents)

    assert len(result.evidence) == 1
    assert result.status == 'partially_verified'
    assert result.supporting_sources == [
        'https://source.com/article'
    ]


# --------------------------------------------------
# RUN VERIFICATION AGENT
# --------------------------------------------------

def test_run_verification_agent_summary(monkeypatch):
    facts = [make_fact() for _ in range(5)]

    statuses = [
        'verified',
        'partially_verified',
        'unverified',
        'contradicted',
        'insufficient_sources'
    ]

    results = [
        va.VerificationResult(
            original_statement=fact.statement,
            status=status,
            explanation='Test explanation'
        )
        for fact, status in zip(facts, statuses)
    ]

    result_iterator = iter(results)

    monkeypatch.setattr(
        va,
        'find_verification_sources',
        lambda fact: []
    )

    monkeypatch.setattr(
        va,
        'extract_verification_documents',
        lambda sources: []
    )

    monkeypatch.setattr(
        va,
        'verify_fact',
        lambda fact, documents: next(result_iterator)
    )

    summary = va.run_verification_agent(facts)

    assert summary.total_facts == 5
    assert summary.verified_count == 1
    assert summary.partially_verified_count == 1
    assert summary.unverified_count == 1
    assert summary.contradicted_count == 1
    assert summary.insufficient_sources_count == 1

    assert (
        summary.verified_count
        + summary.partially_verified_count
        + summary.unverified_count
        + summary.contradicted_count
        + summary.insufficient_sources_count
        == summary.total_facts
    )


def test_run_verification_agent_propagates_errors(monkeypatch):
    monkeypatch.setattr(
        va,
        'find_verification_sources',
        lambda fact: (_ for _ in ()).throw(
            RuntimeError('Search failed')
        )
    )

    with pytest.raises(RuntimeError, match='Search failed'):
        va.run_verification_agent([make_fact()])

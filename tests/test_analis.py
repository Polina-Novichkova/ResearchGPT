import json

import agents.analysis_agent as analysis_agent
import services.embedding_service as embedding_service

from agents.analysis_agent import (
    AnalysisResult,
    Fact,
    NumericData,
    Relevance
)


def make_analysis_result(
    status="relevant",
    source_url="https://example.com/article"
):
    return AnalysisResult(
        title="Test article",
        summary="Test summary",
        key_points=["First point"],
        facts=[
            Fact(
                statement="The mission lasted 378 days.",
                evidence="The mission lasted 378 days.",
                source_url=source_url,
                event_context="CHAPEA Mission 2"
            )
        ],
        numbers=[
            NumericData(
                value="378 days",
                description="Mission duration",
                evidence="The mission lasted 378 days.",
                source_url=source_url
            )
        ],
        relevance=Relevance(
            status=status,
            explanation="Test explanation"
        ),
        source_url=source_url
    )


def test_remove_dupl():
    facts = [
        Fact(
            statement="The mission lasted 378 days.",
            evidence="Evidence 1",
            source_url="url1",
            event_context="Mission 2"
        ),
        Fact(
            statement="The mission lasted 378 days.",
            evidence="Evidence 2",
            source_url="url1",
            event_context="Mission 2"
        ),
        Fact(
            statement="The mission lasted 365 days.",
            evidence="Evidence 3",
            source_url="url2",
            event_context="Mission 2"
        )
    ]

    result = analysis_agent.remove_dupl(
        facts,
        ("statement", "source_url", "event_context")
    )

    assert len(result) == 2


def test_remove_dupl_with_none_values():
    items = [
        Fact(
            statement="Test statement",
            evidence="Evidence",
            event_context="Mission"
        ),
        Fact(
            statement="Test statement",
            evidence="Other evidence",
            event_context="Mission"
        )
    ]

    result = analysis_agent.remove_dupl(
        items,
        ("statement", "source_url", "event_context")
    )

    assert len(result) == 1


def test_validate_evidence():
    source_text = (
        "The mission lasted 378 days. "
        "The crew conducted scientific experiments."
    )

    items = [
        Fact(
            statement="The mission lasted 378 days.",
            evidence="The mission lasted 378 days."
        ),
        Fact(
            statement="The crew had 10 members.",
            evidence="The crew had 10 members."
        )
    ]

    result = analysis_agent.validate_evidence(
        items,
        source_text
    )

    assert len(result) == 1
    assert result[0].statement == "The mission lasted 378 days."


def test_validate_evidence_normalizes_whitespace():
    source_text = "The mission lasted 378 days."

    items = [
        Fact(
            statement="The mission lasted 378 days.",
            evidence="The mission   lasted 378 days."
        )
    ]

    result = analysis_agent.validate_evidence(
        items,
        source_text
    )

    assert len(result) == 1


def test_analyze_doc(monkeypatch):
    document = {
        "url": "https://example.com/article",
        "title": "Test article",
        "content": (
            "The mission lasted 378 days. "
            "The crew conducted scientific experiments."
        )
    }

    response = {
        "title": "Test article",
        "summary": "The mission lasted 378 days.",
        "key_points": [
            "The mission lasted 378 days."
        ],
        "facts": [
            {
                "statement": "The mission lasted 378 days.",
                "evidence": "The mission lasted 378 days.",
                "event_context": "  CHAPEA   Mission 2  "
            },
            {
                "statement": "The crew had 10 members.",
                "evidence": "The crew had 10 members.",
                "event_context": "CHAPEA Mission 2"
            }
        ],
        "numbers": [
            {
                "value": "378 days",
                "description": "Mission duration",
                "evidence": "The mission lasted 378 days."
            }
        ],
        "relevance": {
            "status": "relevant",
            "explanation": "The article answers the question."
        }
    }

    monkeypatch.setattr(
        analysis_agent,
        "generate_response",
        lambda prompt: json.dumps(response)
    )

    result = analysis_agent.analyze_doc(
        document,
        "How long did the mission last?"
    )

    assert result.title == "Test article"
    assert result.source_url == document["url"]

    assert len(result.facts) == 1
    assert result.facts[0].source_url == document["url"]
    assert result.facts[0].event_context == "CHAPEA Mission 2"

    assert len(result.numbers) == 1
    assert result.numbers[0].source_url == document["url"]

    assert result.relevance.status == "relevant"


def test_run_analysis_agent_no_documents(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "create_fact_groups",
        lambda facts: []
    )

    result = analysis_agent.run_analysis_agent(
        [],
        "Test question"
    )

    assert result.relevance_status == "no_sources"
    assert result.summaries == []
    assert result.facts == []
    assert result.numbers == []
    assert result.source_urls == []
    assert result.fact_groups == []


def test_run_analysis_agent_all_analyses_failed(monkeypatch):
    def raise_error(document, subquestion):
        raise RuntimeError("Test analysis error")

    monkeypatch.setattr(
        analysis_agent,
        "analyze_doc",
        raise_error
    )

    monkeypatch.setattr(
        embedding_service,
        "create_fact_groups",
        lambda facts: []
    )

    documents = [
        {"url": "https://example.com/one"},
        {"url": "https://example.com/two"}
    ]

    result = analysis_agent.run_analysis_agent(
        documents,
        "Test question"
    )

    assert result.relevance_status == "analysis_failed"
    assert result.summaries == []
    assert result.facts == []
    assert result.source_urls == []


def test_run_analysis_agent_not_relevant(monkeypatch):
    monkeypatch.setattr(
        analysis_agent,
        "analyze_doc",
        lambda document, subquestion: make_analysis_result(
            status="not_relevant",
            source_url=document["url"]
        )
    )

    monkeypatch.setattr(
        embedding_service,
        "create_fact_groups",
        lambda facts: []
    )

    documents = [
        {"url": "https://example.com/article"}
    ]

    result = analysis_agent.run_analysis_agent(
        documents,
        "Unrelated question"
    )

    assert result.relevance_status == "not_relevant"
    assert result.summaries == []
    assert result.facts == []
    assert result.source_urls == []


def test_run_analysis_agent_relevant(monkeypatch):
    monkeypatch.setattr(
        analysis_agent,
        "analyze_doc",
        lambda document, subquestion: make_analysis_result(
            status="relevant",
            source_url=document["url"]
        )
    )

    monkeypatch.setattr(
        embedding_service,
        "create_fact_groups",
        lambda facts: []
    )

    documents = [
        {"url": "https://example.com/article"}
    ]

    result = analysis_agent.run_analysis_agent(
        documents,
        "Test question"
    )

    assert result.relevance_status == "relevant"
    assert len(result.summaries) == 1
    assert len(result.facts) == 1
    assert len(result.numbers) == 1
    assert result.source_urls == [
        "https://example.com/article"
    ]


def test_run_analysis_agent_mixed_success_and_failure(monkeypatch):
    def fake_analyze(document, subquestion):
        if document["url"].endswith("failed"):
            raise RuntimeError("Test error")

        return make_analysis_result(
            status="relevant",
            source_url=document["url"]
        )

    monkeypatch.setattr(
        analysis_agent,
        "analyze_doc",
        fake_analyze
    )

    monkeypatch.setattr(
        embedding_service,
        "create_fact_groups",
        lambda facts: []
    )

    documents = [
        {"url": "https://example.com/failed"},
        {"url": "https://example.com/success"}
    ]

    result = analysis_agent.run_analysis_agent(
        documents,
        "Test question"
    )

    assert result.relevance_status == "relevant"
    assert len(result.summaries) == 1
    assert result.source_urls == [
        "https://example.com/success"
    ]

import numpy as np
import pytest

import services.embedding_service as embedding_service
from agents.analysis_agent import Fact


def make_fact(
    statement,
    event_context="CHAPEA Mission 2",
    source_url="https://example.com/article"
):
    return Fact(
        statement=statement,
        evidence=statement,
        event_context=event_context,
        source_url=source_url
    )


@pytest.mark.parametrize(
    "text, expected",
    [
        ("378 days", [378]),
        ("3.5 million", [3.5]),
        ("3,5 million", [3.5]),
        ("1,500 people", [1500]),
        ("1,500.5 meters", [1500.5]),
        ("-12 degrees", [-12]),
    ]
)
def test_extract_numbers(text, expected):
    assert embedding_service.extract_numbers(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("378 days", ["day"]),
        ("20 percent", ["percent"]),
        ("20%", ["percent"]),
        ("50 человек", ["person"]),
        ("120 square meters", ["square_meter"]),
        ("10 kilometers", ["kilometer"]),
        ("5 kilograms", ["kilogram"]),
    ]
)
def test_extract_units(text, expected):
    assert embedding_service.extract_units(text) == expected


def test_have_same_numbers():
    assert embedding_service.have_same_numbers(
        "The mission lasted 378 days",
        "The crew spent 378 days there"
    )

    assert not embedding_service.have_same_numbers(
        "The mission lasted 378 days",
        "The mission lasted 365 days"
    )


def test_have_same_units():
    assert embedding_service.have_same_units(
        "The mission lasted 378 days",
        "The mission lasted 365 days"
    )

    assert not embedding_service.have_same_units(
        "The distance was 100 kilometers",
        "The distance was 100 miles"
    )


def test_have_same_event_context():
    assert embedding_service.have_same_event_context(
        "CHAPEA Mission 2",
        "  CHAPEA   Mission 2  "
    )

    assert not embedding_service.have_same_event_context(
        "CHAPEA Mission 1",
        "CHAPEA Mission 2"
    )

    assert not embedding_service.have_same_event_context(
        "",
        "CHAPEA Mission 2"
    )


def test_compare_facts_with_same_information(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: np.array([[1.0, 0.0], [1.0, 0.0]])
    )

    fact_1 = make_fact("The mission lasted 378 days.")
    fact_2 = make_fact("The crew spent 378 days on the mission.")

    result = embedding_service.compare_facts(fact_1, fact_2)

    assert result["is_similar"] is True
    assert result["same_numbers"] is True
    assert result["same_units"] is True
    assert result["same_event"] is True


def test_compare_facts_with_different_numbers(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: np.array([[1.0, 0.0], [1.0, 0.0]])
    )

    fact_1 = make_fact("The mission lasted 378 days.")
    fact_2 = make_fact("The mission lasted 365 days.")

    result = embedding_service.compare_facts(fact_1, fact_2)

    assert result["same_numbers"] is False
    assert result["numbers_compatible"] is False
    assert result["is_similar"] is False


def test_compare_facts_with_different_units(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: np.array([[1.0, 0.0], [1.0, 0.0]])
    )

    fact_1 = make_fact("The distance was 100 kilometers.")
    fact_2 = make_fact("The distance was 100 miles.")

    result = embedding_service.compare_facts(fact_1, fact_2)

    assert result["same_units"] is False
    assert result["units_compatible"] is False
    assert result["is_similar"] is False


def test_compare_facts_with_different_events(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: np.array([[1.0, 0.0], [1.0, 0.0]])
    )

    fact_1 = make_fact(
        "The mission lasted 378 days.",
        event_context="CHAPEA Mission 1"
    )

    fact_2 = make_fact(
        "The mission lasted 378 days.",
        event_context="CHAPEA Mission 2"
    )

    result = embedding_service.compare_facts(fact_1, fact_2)

    assert result["same_event"] is False
    assert result["is_similar"] is False


def test_group_dupl_facts(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: np.tile([1.0, 0.0], (len(texts), 1))
    )

    fact_1 = make_fact(
        "The mission lasted 378 days.",
        source_url="https://example.com/one"
    )

    fact_2 = make_fact(
        "The crew spent 378 days on the mission.",
        source_url="https://example.com/two"
    )

    fact_3 = make_fact(
        "The mission lasted 365 days.",
        source_url="https://example.com/three"
    )

    groups = embedding_service.group_dupl_facts(
        [fact_1, fact_2, fact_3]
    )

    assert len(groups) == 1
    assert len(groups[0]) == 2
    assert fact_1 in groups[0]
    assert fact_2 in groups[0]
    assert fact_3 not in groups[0]


def test_create_fact_groups(monkeypatch):
    monkeypatch.setattr(
        embedding_service,
        "generate_embeddings",
        lambda texts: np.tile([1.0, 0.0], (len(texts), 1))
    )

    fact_1 = make_fact(
        "The mission lasted 378 days.",
        source_url="https://example.com/one"
    )

    fact_2 = make_fact(
        "The crew spent 378 days on the mission.",
        source_url="https://example.com/two"
    )

    groups = embedding_service.create_fact_groups(
        [fact_1, fact_2]
    )

    assert len(groups) == 1

    group = groups[0]

    assert len(group.facts) == 2
    assert group.statement == fact_1.statement
    assert group.event_context == fact_1.event_context
    assert group.source_urls == [
        "https://example.com/one",
        "https://example.com/two"
    ]


def test_empty_fact_list():
    assert embedding_service.group_dupl_facts([]) == []
    assert embedding_service.create_fact_groups([]) == []

from crossword_agent.tools.clue_solver import (
    CANDIDATE_RESPONSE_FORMAT,
    _parse_candidate_response,
    classify_clue,
    clue_type_hint,
    filter_candidates,
)


def test_openai_response_format_uses_strict_json_schema():
    assert CANDIDATE_RESPONSE_FORMAT["type"] == "json_schema"
    schema_spec = CANDIDATE_RESPONSE_FORMAT["json_schema"]
    assert schema_spec["strict"] is True
    assert schema_spec["schema"]["additionalProperties"] is False
    assert schema_spec["schema"]["required"] == ["candidates"]


def test_parse_candidate_response_rejects_extra_fields():
    content = """
    {
      "candidates": [
        {"answer": "CAT", "confidence": 0.9, "rationale": "feline", "extra": "bad"}
      ]
    }
    """
    assert _parse_candidate_response(content, limit=5) == []


def test_parse_candidate_response_and_filter_candidates():
    content = """
    {
      "candidates": [
        {"answer": "CAR", "confidence": 0.8, "rationale": "wrong crossing"},
        {"answer": "CAT", "confidence": 0.7, "rationale": "feline pet"},
        {"answer": "CATER", "confidence": 0.6, "rationale": "too long"}
      ]
    }
    """
    parsed = _parse_candidate_response(content, limit=5)
    filtered = filter_candidates(parsed, length=3, pattern="__T")
    assert [candidate.answer for candidate in filtered] == ["CAT"]


def test_classify_clue_adds_type_aware_prompt_signal():
    assert classify_clue("Present plural of be") == "grammar"
    assert classify_clue("Company head, for short") == "abbreviation"
    assert classify_clue("Pun clue?") == "wordplay"
    assert "tense" in clue_type_hint("grammar")

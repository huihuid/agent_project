from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from crossword_agent.domain.models import AgentConfig, Candidate, Slot, ToolCallStats


MOCK_BANK: dict[str, list[str]] = {
    "one who bakes": ["BAKER"],
    "breakfast grain": ["OATS"],
    "not false": ["TRUE"],
    "opposite of out": ["IN"],
    "feline pet": ["CAR", "CAT"],
    "canine pet": ["DIG", "DOG"],
    "present plural of be": ["ARE"],
    "number after nine": ["TEN"],
    "metal-bearing rock": ["ORE"],
    "obtain": ["GET"],
    "river through paris": ["SEINE"],
    "color of a clear sky": ["BLUE"],
    "frozen water": ["ICE"],
    "large body of salt water": ["OCEAN"],
    "not closed": ["OPEN"],
    "small songbird": ["WREN"],
    "quick sleep": ["NAP"],
    "used to unlock a door": ["KEY"],
    "object thrown or kicked in games": ["BALL"],
    "region or space": ["AREA"],
    "guide or be in front": ["LEAD"],
    "polite term for a woman": ["LADY"],
    "organ that pumps blood": ["HEART"],
    "glowing piece of coal": ["EMBER"],
    "mistreat": ["ABUSE"],
    "sticky tree substance": ["RESIN"],
    "general direction": ["TREND"],
}


class CandidateItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(description="Uppercase A-Z crossword answer candidate.")
    confidence: float = Field(ge=0.0, le=1.0, description="Estimated probability that this candidate is correct.")
    rationale: str = Field(description="Brief clue reasoning for debugging.")


class CandidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[CandidateItem] = Field(description="Ranked answer candidates.")


CANDIDATE_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "crossword_clue_candidates",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["candidates"],
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["answer", "confidence", "rationale"],
                        "properties": {
                            "answer": {
                                "type": "string",
                                "description": "Uppercase A-Z crossword answer candidate.",
                            },
                            "confidence": {
                                "type": "number",
                                "description": "Estimated probability that this candidate is correct.",
                            },
                            "rationale": {
                                "type": "string",
                                "description": "Brief clue reasoning for debugging.",
                            },
                        },
                    },
                }
            },
        },
    },
}


@dataclass
class ClueSolverTool:
    config: AgentConfig

    def run(self, slot: Slot, pattern: str, stats: ToolCallStats) -> list[Candidate]:
        if self.config.mock or not os.getenv("OPENAI_API_KEY"):
            return self._mock(slot, pattern)
        if stats.llm_calls >= self.config.max_llm_calls:
            return []
        return self._llm(slot, pattern, stats)

    def _mock(self, slot: Slot, pattern: str) -> list[Candidate]:
        key = slot.clue.lower().strip()
        answers = MOCK_BANK.get(key, [])
        candidates = [
            Candidate(answer=answer, confidence=0.95, source="mock", rationale="Matched built-in demo clue.")
            for answer in answers
        ]
        if not candidates:
            candidates.append(Candidate(answer="".join("A" if c == "_" else c for c in pattern), confidence=0.05, source="mock"))
        return filter_candidates(candidates, slot.length, pattern)

    def _llm(self, slot: Slot, pattern: str, stats: ToolCallStats) -> list[Candidate]:
        from openai import OpenAI

        client = OpenAI()
        prompt = {
            "clue": slot.clue,
            "clue_type": classify_clue(slot.clue),
            "clue_type_hint": clue_type_hint(classify_clue(slot.clue)),
            "length": slot.length,
            "known_pattern": pattern,
            "candidate_count": self.config.candidates_per_clue,
            "instructions": (
                "Return ranked crossword answer candidates. Answers must use uppercase A-Z only, "
                "must exactly match length, and must satisfy known_pattern where underscores are unknown."
            ),
        }
        response = client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            response_format=CANDIDATE_RESPONSE_FORMAT,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You solve American-style crossword clues. Treat answer length and known pattern "
                        "as hard constraints. Return only data that conforms to the provided JSON schema."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
        )
        stats.llm_calls += 1
        usage = response.usage
        if usage:
            stats.prompt_tokens += usage.prompt_tokens or 0
            stats.completion_tokens += usage.completion_tokens or 0
            # Conservative placeholder. Exact pricing changes; this keeps budget accounting visible.
            stats.estimated_cost_usd += ((usage.prompt_tokens or 0) + (usage.completion_tokens or 0)) * 0.000001

        content = response.choices[0].message.content or "{}"
        candidates = _parse_candidate_response(content, self.config.candidates_per_clue)
        return filter_candidates(candidates, slot.length, pattern)


def filter_candidates(candidates: list[Candidate], length: int, pattern: str) -> list[Candidate]:
    out: list[Candidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        answer = re.sub(r"[^A-Za-z]", "", candidate.answer).upper()
        if len(answer) != length or answer in seen:
            continue
        if any(p != "_" and p != a for p, a in zip(pattern, answer)):
            continue
        seen.add(answer)
        out.append(Candidate(answer, max(0.0, min(1.0, candidate.confidence)), candidate.source, candidate.rationale))
    return sorted(out, key=lambda item: item.confidence, reverse=True)


def classify_clue(clue: str) -> str:
    normalized = clue.strip().lower()
    if "___" in normalized or "_" in normalized:
        return "fill_in_blank"
    if "abbr." in normalized or "briefly" in normalized or "for short" in normalized:
        return "abbreviation"
    if normalized.endswith("?"):
        return "wordplay"
    if any(token in normalized for token in ("past tense", "plural", "present", "comparative", "superlative")):
        return "grammar"
    if any(char.isupper() for char in clue[1:]):
        return "proper_noun"
    return "literal"


def clue_type_hint(clue_type: str) -> str:
    hints = {
        "fill_in_blank": "Preserve the phrase's grammar and fill the missing word exactly.",
        "abbreviation": "Consider standard crossword abbreviations and short forms.",
        "wordplay": "Consider puns, alternate meanings, and non-literal readings.",
        "grammar": "Match tense, number, and part of speech before ranking synonyms.",
        "proper_noun": "Consider named entities, titles, places, and people.",
        "literal": "Prefer direct synonyms or definitions before obscure alternatives.",
    }
    return hints.get(clue_type, hints["literal"])


def _parse_candidate_response(content: str, limit: int) -> list[Candidate]:
    data = _parse_json(content)
    try:
        parsed = CandidateResponse.model_validate(data)
    except ValidationError:
        return []
    return [
        Candidate(
            answer=item.answer,
            confidence=item.confidence,
            source="llm",
            rationale=item.rationale,
        )
        for item in parsed.candidates[:limit]
    ]


def _parse_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

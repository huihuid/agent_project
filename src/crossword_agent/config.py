from __future__ import annotations

from pathlib import Path

import yaml

from crossword_agent.domain.models import AgentConfig


def load_config(path: str | None = None, **overrides) -> AgentConfig:
    data = {}
    if path:
        data = yaml.safe_load(Path(path).read_text()) or {}
    data.update({key: value for key, value in overrides.items() if value is not None})
    return AgentConfig(**data)

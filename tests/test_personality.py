import pytest
from agent.personality import (
    BASE_SYSTEM_PROMPT,
    PersonalityConfig,
    get_effective_system_prompt,
    get_personality,
    set_personality,
)


def test_default_personality():
    p = get_personality()
    assert p.name == "Chorus"
    assert p.role == "Personal AI Assistant"
    assert len(p.system_prompt) > 0
    assert "Calendar" in p.system_prompt
    assert "Email" in p.system_prompt
    assert "Docs and knowledge search" in p.system_prompt
    assert get_effective_system_prompt() == BASE_SYSTEM_PROMPT.strip()


def test_set_personality():
    custom = PersonalityConfig(name="TestBot", role="Tester", tone="formal", system_prompt="You are a test bot.")
    set_personality(custom)
    p = get_personality()
    assert p.name == "TestBot"
    assert p.role == "Tester"
    assert p.system_prompt == "You are a test bot."

    from agent.personality import DEFAULT_PERSONALITY
    set_personality(DEFAULT_PERSONALITY)

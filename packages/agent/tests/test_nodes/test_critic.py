import json

import copilot.agent.nodes.critic as critic_module
from copilot.agent.nodes.critic import critic_node
from copilot.agent.state import RefinementType, create_initial_state


def make_state(iteration=1, max_iterations=3, **overrides):
    state = create_initial_state("How is Microsoft's cloud strategy evolving?")
    state["iteration"] = iteration
    state["max_iterations"] = max_iterations
    state["synthesis"] = "Some synthesis text"
    state.update(overrides)
    return state


def test_critic_requests_refinement(fake_llm_factory):
    critique = {
        "quality_score": 0.4,
        "is_sufficient": False,
        "gaps_identified": ["missing recent data"],
        "refinement_tool": "web_search",
        "refinement_query": "Microsoft cloud strategy 2026",
        "reasoning": "needs current info",
    }
    fake_llm_factory(critic_module, json.dumps(critique))

    result = critic_node(make_state(iteration=1))

    assert result["needs_refinement"] is True
    assert result["refinement_type"] == RefinementType.WEB_SEARCH.value
    assert result["refinement_focus"] == "Microsoft cloud strategy 2026"
    assert result["iteration"] == 2  # incremented on loop-back


def test_critic_proceeds_when_sufficient(fake_llm_factory):
    critique = {
        "quality_score": 0.9,
        "is_sufficient": True,
        "gaps_identified": [],
        "refinement_tool": "none",
        "refinement_query": "",
        "reasoning": "good enough",
    }
    fake_llm_factory(critic_module, json.dumps(critique))

    result = critic_node(make_state(iteration=1))

    assert result["needs_refinement"] is False
    assert result["refinement_type"] == RefinementType.NONE.value
    assert "iteration" not in result  # no increment when proceeding


def test_critic_forces_proceed_at_max_iterations(fake_llm_factory):
    llm = fake_llm_factory(critic_module, "should never be called")

    result = critic_node(make_state(iteration=3, max_iterations=3))

    assert result["needs_refinement"] is False
    assert result["critique"]["is_sufficient"] is True
    assert llm.prompts == []  # short-circuits before any LLM call


def test_critic_parse_failure_falls_back_to_proceed(fake_llm_factory):
    fake_llm_factory(critic_module, "not json at all")

    result = critic_node(make_state(iteration=1))

    assert result["needs_refinement"] is False
    assert result["quality_score"] == 0.7


def test_critic_unknown_tool_maps_to_none(fake_llm_factory):
    critique = {
        "quality_score": 0.5,
        "is_sufficient": False,
        "refinement_tool": "teleport",
        "refinement_query": "x",
        "reasoning": "?",
    }
    fake_llm_factory(critic_module, json.dumps(critique))

    result = critic_node(make_state(iteration=1))

    # Unknown tool → NONE → no refinement loop
    assert result["needs_refinement"] is False
    assert result["refinement_type"] == RefinementType.NONE.value

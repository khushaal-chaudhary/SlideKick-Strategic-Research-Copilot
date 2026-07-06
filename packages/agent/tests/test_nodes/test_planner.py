import json

import copilot.agent.nodes.planner as planner_module
from copilot.agent.nodes.planner import _parse_plan_response, planner_node
from copilot.agent.state import (
    OutputFormat,
    QueryType,
    RetrievalStrategy,
    create_initial_state,
)

VALID_PLAN = {
    "query_type": "financial",
    "entities_of_interest": ["Microsoft", "Apple"],
    "stock_symbols": ["MSFT", "AAPL"],
    "retrieval_strategy": "financial_first",
    "output_format": "chat",
    "research_plan": [
        {"step": 1, "description": "Compare P/E", "query": "MSFT AAPL P/E comparison"}
    ],
    "reasoning": "financial comparison",
}


def test_planner_happy_path(fake_llm_factory):
    fake_llm_factory(planner_module, json.dumps(VALID_PLAN))
    state = create_initial_state("Compare MSFT and AAPL P/E ratios")

    result = planner_node(state)

    assert result["query_type"] == QueryType.FINANCIAL.value
    assert result["retrieval_strategy"] == RetrievalStrategy.FINANCIAL_FIRST.value
    assert result["entities_of_interest"] == ["Microsoft", "Apple"]
    assert result["stock_symbols"] == ["MSFT", "AAPL"]
    assert result["research_plan"][0]["query"] == "MSFT AAPL P/E comparison"
    assert result["research_plan"][0]["status"] == "pending"
    assert result["iteration"] == 1


def test_planner_handles_markdown_fenced_json(fake_llm_factory):
    fenced = "```json\n" + json.dumps(VALID_PLAN) + "\n```"
    fake_llm_factory(planner_module, fenced)
    result = planner_node(create_initial_state("q"))
    assert result["query_type"] == QueryType.FINANCIAL.value


def test_planner_falls_back_on_garbage_response(fake_llm_factory):
    fake_llm_factory(planner_module, "I cannot answer in JSON, sorry!")
    state = create_initial_state("some query")

    result = planner_node(state)

    assert result["query_type"] == QueryType.UNKNOWN.value
    assert result["retrieval_strategy"] == RetrievalStrategy.HYBRID.value
    # Fallback plan must still contain one executable step with the original query
    assert len(result["research_plan"]) == 1
    assert result["research_plan"][0]["query"] == "some query"


def test_planner_normalizes_invalid_enum_values(fake_llm_factory):
    bad = dict(VALID_PLAN, query_type="nonsense", retrieval_strategy="bogus", output_format="pdf")
    fake_llm_factory(planner_module, json.dumps(bad))

    result = planner_node(create_initial_state("q"))

    assert result["query_type"] == QueryType.UNKNOWN.value
    assert result["retrieval_strategy"] == RetrievalStrategy.HYBRID.value
    assert result["output_format"] == OutputFormat.CHAT.value


def test_parse_plan_extracts_embedded_json():
    text = "Here is the plan: " + json.dumps(VALID_PLAN) + " hope that helps"
    parsed = _parse_plan_response(text)
    assert parsed["query_type"] == "financial"

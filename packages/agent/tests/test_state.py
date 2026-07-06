from copilot.agent.state import (
    OutputFormat,
    QueryType,
    RefinementType,
    RetrievalStrategy,
    create_initial_state,
    state_summary,
)


def test_initial_state_defaults():
    state = create_initial_state("What did Microsoft do in 2023?")
    assert state["original_query"] == "What did Microsoft do in 2023?"
    assert state["query_type"] == QueryType.UNKNOWN.value
    assert state["retrieval_strategy"] == RetrievalStrategy.HYBRID.value
    assert state["output_format"] == OutputFormat.CHAT.value
    assert state["refinement_type"] == RefinementType.NONE.value
    assert state["iteration"] == 0
    assert state["max_iterations"] == 3
    assert state["needs_refinement"] is False
    assert state["graph_results"] == []
    assert state["error"] is None


def test_initial_state_custom_max_iterations():
    state = create_initial_state("q", max_iterations=5)
    assert state["max_iterations"] == 5


def test_state_summary_renders():
    state = create_initial_state("A query about Azure growth")
    summary = state_summary(state)
    assert "A query about Azure growth" in summary
    assert "0/3" in summary


def test_enum_values_are_strings():
    # Enum values are persisted into state as raw strings; keep them stable
    assert QueryType.FINANCIAL.value == "financial"
    assert RetrievalStrategy.FINANCIAL_FIRST.value == "financial_first"
    assert RefinementType.WEB_SEARCH.value == "web_search"
    assert OutputFormat.SLIDES.value == "slides"

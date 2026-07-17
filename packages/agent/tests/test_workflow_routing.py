from copilot.agent.workflow import (
    route_after_critic,
    route_retrieval,
    should_continue_research,
)


def test_loops_back_when_refinement_needed_and_iterations_remain():
    state = {"needs_refinement": True, "iteration": 1, "max_iterations": 3}
    assert should_continue_research(state) == "retrieve"


def test_proceeds_when_no_refinement_needed():
    state = {"needs_refinement": False, "iteration": 1, "max_iterations": 3}
    assert should_continue_research(state) == "generator"


def test_proceeds_at_max_iterations_even_if_refinement_requested():
    state = {"needs_refinement": True, "iteration": 3, "max_iterations": 3}
    assert should_continue_research(state) == "generator"


def test_proceeds_past_max_iterations():
    state = {"needs_refinement": True, "iteration": 4, "max_iterations": 3}
    assert should_continue_research(state) == "generator"


def test_defaults_to_generator_on_empty_state():
    assert should_continue_research({}) == "generator"


# =============================================================================
# First-pass retrieval fan-out
# =============================================================================


def test_hybrid_fans_out_to_graph_and_vector_in_parallel():
    assert route_retrieval({"retrieval_strategy": "hybrid"}) == [
        "graph_retrieval",
        "vector_retrieval",
    ]


def test_default_strategy_is_hybrid_fan_out():
    assert route_retrieval({}) == ["graph_retrieval", "vector_retrieval"]


def test_financial_first_with_symbols_runs_financial_and_graph():
    state = {"retrieval_strategy": "financial_first", "stock_symbols": ["MSFT"]}
    assert route_retrieval(state) == ["financial_retrieval", "graph_retrieval"]


def test_financial_first_without_symbols_falls_back_to_graph():
    state = {"retrieval_strategy": "financial_first", "stock_symbols": []}
    assert route_retrieval(state) == ["graph_retrieval"]


def test_single_source_strategies():
    assert route_retrieval({"retrieval_strategy": "vector_only"}) == ["vector_retrieval"]
    assert route_retrieval({"retrieval_strategy": "web_only"}) == ["web_retrieval"]
    assert route_retrieval({"retrieval_strategy": "graph_only"}) == ["graph_retrieval"]


# =============================================================================
# Critic refinement routing
# =============================================================================


def test_critic_routes_refinement_to_requested_tool():
    state = {
        "needs_refinement": True,
        "iteration": 1,
        "max_iterations": 3,
        "refinement_type": "web_search",
    }
    assert route_after_critic(state) == ["web_retrieval"]


def test_critic_routes_unknown_refinement_to_graph():
    state = {
        "needs_refinement": True,
        "iteration": 1,
        "max_iterations": 3,
        "refinement_type": "something_new",
    }
    assert route_after_critic(state) == ["graph_retrieval"]


def test_critic_routes_to_generator_when_sufficient():
    state = {"needs_refinement": False, "iteration": 1, "max_iterations": 3}
    assert route_after_critic(state) == ["generator"]

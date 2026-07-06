from copilot.agent.workflow import should_continue_research


def test_loops_back_when_refinement_needed_and_iterations_remain():
    state = {"needs_refinement": True, "iteration": 1, "max_iterations": 3}
    assert should_continue_research(state) == "retriever"


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

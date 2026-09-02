from types import SimpleNamespace

import pytest

from jiuwenswarm.agents.harness.team.topology import (
    apply_team_routing_to_spec,
    build_team_routing_prompt,
    route_team_query,
    team_routing_config_from_dict,
)


def _enabled_config(**overrides):
    return team_routing_config_from_dict({"enabled": True, **overrides})


def test_team_router_is_disabled_by_default():
    config = team_routing_config_from_dict({})

    assert route_team_query("Implement this in parallel", config) is None


def test_router_selects_parallel_topology_then_allocates_roles():
    decision = route_team_query(
        "Implement multiple independent software components in parallel",
        _enabled_config(),
    )

    assert decision is not None
    assert decision.topology == "parallel"
    assert "implementer" in decision.roles
    assert decision.dispatch_mode == "autonomous"
    assert decision.fallback_reason == ""


def test_review_topology_always_allocates_reviewer():
    decision = route_team_query(
        "Audit this implementation and verify its correctness",
        _enabled_config(),
    )

    assert decision is not None
    assert decision.topology == "review"
    assert "reviewer" in decision.roles
    assert decision.enable_verification is True
    assert decision.dispatch_mode == "scheduled"


def test_low_confidence_uses_configured_team_topology_fallback():
    decision = route_team_query("Tell me something", _enabled_config())

    assert decision is not None
    assert decision.topology == "sequential"
    assert decision.roles == ("generalist",)
    assert decision.fallback_reason == "low_topology_confidence"


def test_decision_applies_runtime_supported_topology_fields():
    decision = route_team_query(
        "Review and verify the implementation",
        _enabled_config(),
    )
    spec = SimpleNamespace(
        dispatch_mode="autonomous",
        enable_task_verification=False,
        default_max_review_rounds=3,
        metadata={"existing": True},
    )

    apply_team_routing_to_spec(spec, decision)

    assert spec.dispatch_mode == "scheduled"
    assert spec.enable_task_verification is True
    assert spec.default_max_review_rounds == 2
    assert spec.metadata["existing"] is True
    assert spec.metadata["team_routing"]["topology"] == "review"


def test_routing_prompt_preserves_human_member_sender_prefix():
    decision = route_team_query(
        "Implement multiple independent components in parallel",
        _enabled_config(),
    )

    prompt = build_team_routing_prompt("$reviewer-1 check this", decision)

    assert prompt.startswith("$reviewer-1 [Team routing directive]")
    assert "Topology: parallel" in prompt
    assert "[User query]\ncheck this" in prompt


def test_config_rejects_duplicate_topology_ids():
    with pytest.raises(ValueError, match="Duplicate team routing topology"):
        team_routing_config_from_dict(
            {
                "topologies": [
                    {"id": "same", "description": "one"},
                    {"id": "same", "description": "two"},
                ],
                "default_topology": "same",
            }
        )

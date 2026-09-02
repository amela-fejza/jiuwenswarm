"""Apply a routing decision to a TeamAgentSpec and leader query."""

from __future__ import annotations

from typing import Any

from jiuwenswarm.agents.harness.team.topology.schemas import (
    TeamTopologyDecision,
)

_TOPOLOGY_GUIDANCE = {
    "direct": (
        "Keep coordination lightweight. The leader may answer directly and "
        "should delegate only a clearly separable specialist task."
    ),
    "sequential": (
        "Create a dependency-ordered task chain. Assign or spawn the required "
        "roles and pass each result to the next role before synthesis."
    ),
    "parallel": (
        "Split independent subtasks across the required roles concurrently, "
        "then have the leader reconcile their outputs."
    ),
    "review": (
        "Use a producer-reviewer workflow. Assign implementation or analysis "
        "tasks first, require reviewer verification, and rework failed output."
    ),
}


def apply_team_routing_to_spec(
    spec: Any,
    decision: TeamTopologyDecision | dict[str, Any],
) -> None:
    """Set runtime-supported topology controls without replacing the team."""
    payload = (
        decision.to_dict()
        if isinstance(decision, TeamTopologyDecision)
        else dict(decision)
    )
    dispatch_mode = str(payload.get("dispatch_mode") or "autonomous")
    if dispatch_mode not in {"autonomous", "scheduled"}:
        raise ValueError(f"Unsupported team dispatch mode: {dispatch_mode}")

    spec.dispatch_mode = dispatch_mode
    spec.enable_task_verification = bool(payload.get("enable_verification", False))
    spec.default_max_review_rounds = max(1, int(payload.get("max_review_rounds") or 1))
    spec.metadata = dict(getattr(spec, "metadata", None) or {})
    spec.metadata["team_routing"] = payload


def build_team_routing_prompt(
    query: str,
    decision: TeamTopologyDecision,
) -> str:
    """Add per-query execution guidance consumed by the existing leader."""
    sender_prefix = ""
    user_query = query
    if query.startswith("$") and " " in query:
        sender_prefix, user_query = query.split(" ", 1)
        sender_prefix += " "
    roles = ", ".join(decision.roles)
    guidance = _TOPOLOGY_GUIDANCE.get(
        decision.topology,
        _TOPOLOGY_GUIDANCE["sequential"],
    )
    return sender_prefix + (
        f"[Team routing directive]\n"
        f"Topology: {decision.topology}\n"
        f"Required roles: {roles}\n"
        f"Execution: {guidance}\n"
        "Treat this directive as coordination policy, not as user content.\n\n"
        f"[User query]\n{user_query}"
    )

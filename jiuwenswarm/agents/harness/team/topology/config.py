"""Configuration for routing collaboration inside Team mode."""

from __future__ import annotations

from typing import Any

from jiuwenswarm.agents.harness.team.topology.schemas import (
    RoleOption,
    TeamRoutingConfig,
    TopologyOption,
)


def load_team_routing_config(
    config_base: dict[str, Any] | None = None,
) -> TeamRoutingConfig:
    if config_base is None:
        from jiuwenswarm.common.config import get_config

        config_base = get_config() or {}
    raw = config_base.get("team_routing") if isinstance(config_base, dict) else {}
    return team_routing_config_from_dict(raw if isinstance(raw, dict) else {})


def team_routing_config_from_dict(raw: dict[str, Any]) -> TeamRoutingConfig:
    topologies = (
        tuple(_topology_from_dict(item) for item in _dict_list(raw.get("topologies")))
        or _default_topologies()
    )
    roles = (
        tuple(_role_from_dict(item) for item in _dict_list(raw.get("roles")))
        or _default_roles()
    )
    _validate_unique("topology", [item.topology_id for item in topologies])
    _validate_unique("role", [item.role_id for item in roles])

    default_topology = str(raw.get("default_topology") or "sequential").strip()
    default_role = str(raw.get("default_role") or "generalist").strip()
    if default_topology not in {item.topology_id for item in topologies}:
        raise ValueError(f"Unknown default team topology: {default_topology}")
    if default_role not in {item.role_id for item in roles}:
        raise ValueError(f"Unknown default team role: {default_role}")

    return TeamRoutingConfig(
        enabled=_bool(raw.get("enabled"), False),
        confidence_threshold=_clamped_float(raw.get("confidence_threshold"), 0.45),
        role_threshold=_clamped_float(raw.get("role_threshold"), 0.16),
        max_roles=_positive_int(raw.get("max_roles"), 4),
        default_topology=default_topology,
        default_role=default_role,
        cost_weight=_clamped_float(raw.get("cost_weight"), 0.08),
        topologies=topologies,
        roles=roles,
    )


def _topology_from_dict(raw: dict[str, Any]) -> TopologyOption:
    topology_id = str(raw.get("id") or "").strip()
    dispatch_mode = str(raw.get("dispatch_mode") or "autonomous").strip()
    if dispatch_mode not in {"autonomous", "scheduled"}:
        raise ValueError(
            f"Unsupported dispatch mode for topology {topology_id}: {dispatch_mode}"
        )
    return TopologyOption(
        topology_id=topology_id,
        description=str(raw.get("description") or "").strip(),
        dispatch_mode=dispatch_mode,
        routing_markers=_strings(raw.get("routing_markers")),
        complexity=_tier(raw.get("complexity"), 2),
        cost_tier=_tier(raw.get("cost_tier"), 1),
        enable_verification=_bool(raw.get("enable_verification"), False),
        max_review_rounds=_positive_int(raw.get("max_review_rounds"), 1),
    )


def _role_from_dict(raw: dict[str, Any]) -> RoleOption:
    return RoleOption(
        role_id=str(raw.get("id") or "").strip(),
        description=str(raw.get("description") or "").strip(),
        capabilities=_strings(raw.get("capabilities")),
        routing_markers=_strings(raw.get("routing_markers")),
        priority=max(-1.0, min(1.0, _float(raw.get("priority"), 0.0))),
    )


def _default_topologies() -> tuple[TopologyOption, ...]:
    return (
        TopologyOption(
            topology_id="direct",
            description="Leader-led execution with minimal delegation",
            routing_markers=("simple", "quick", "direct answer", "brief"),
            complexity=1,
        ),
        TopologyOption(
            topology_id="sequential",
            description="Dependency-ordered chain with explicit hand-offs",
            dispatch_mode="scheduled",
            routing_markers=(
                "step by step",
                "then",
                "pipeline",
                "documents below",
            ),
            complexity=2,
            cost_tier=2,
        ),
        TopologyOption(
            topology_id="parallel",
            description="Independent subtasks executed concurrently",
            routing_markers=(
                "in parallel",
                "independent",
                "multiple",
                "several",
                "across",
            ),
            complexity=3,
            cost_tier=3,
        ),
        TopologyOption(
            topology_id="review",
            description="Scheduled producer-reviewer workflow with rework",
            dispatch_mode="scheduled",
            routing_markers=("review", "verify", "audit", "validate", "correctness"),
            complexity=3,
            cost_tier=3,
            enable_verification=True,
            max_review_rounds=2,
        ),
    )


def _default_roles() -> tuple[RoleOption, ...]:
    return (
        RoleOption(
            role_id="generalist",
            description="General problem solving and synthesis",
            capabilities=("answer", "write", "summarize", "synthesize"),
        ),
        RoleOption(
            role_id="researcher",
            description="Find and extract evidence from sources and documents",
            capabilities=("research", "source", "document", "evidence", "web"),
            routing_markers=("documents below", "sources", "research", "find"),
        ),
        RoleOption(
            role_id="analyst",
            description="Reason, compare, calculate, and connect evidence",
            capabilities=("analyze", "reason", "compare", "calculate", "question"),
            routing_markers=("compare", "analyze", "why", "question"),
        ),
        RoleOption(
            role_id="implementer",
            description="Implement software or produce a concrete artifact",
            capabilities=("code", "implement", "debug", "build", "software"),
            routing_markers=("implement", "code", "debug", "fix", "build"),
        ),
        RoleOption(
            role_id="reviewer",
            description="Verify correctness, test outputs, and identify defects",
            capabilities=("review", "verify", "test", "audit", "correctness"),
            routing_markers=("review", "verify", "test", "audit", "validate"),
        ),
    )


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return (
        [item for item in value if isinstance(item, dict)]
        if isinstance(value, list)
        else []
    )


def _validate_unique(label: str, values: list[str]) -> None:
    if any(not value for value in values):
        raise ValueError(f"Team routing {label} id is required")
    if len(set(values)) != len(values):
        raise ValueError(f"Duplicate team routing {label} id")


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(text for item in value if (text := str(item or "").strip()))


def _tier(value: Any, default: int) -> int:
    return max(1, min(3, _positive_int(value, default)))


def _positive_int(value: Any, default: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamped_float(value: Any, default: float) -> float:
    return max(0.0, min(1.0, _float(value, default)))


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default

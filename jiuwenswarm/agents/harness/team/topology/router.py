"""Two-stage rules router for collaboration topology and team roles."""

from __future__ import annotations

import math
import re
import time
from collections.abc import Iterable

from jiuwenswarm.agents.harness.team.topology.schemas import (
    RoleOption,
    RoutingScore,
    TeamRoutingConfig,
    TeamTopologyDecision,
    TopologyOption,
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9_+-]+")
_COMPLEXITY_MARKERS = (
    "multiple",
    "several",
    "compare",
    "across",
    "end-to-end",
    "architecture",
    "comprehensive",
    "step by step",
)


def route_team_query(
    query: str,
    config: TeamRoutingConfig,
) -> TeamTopologyDecision | None:
    """Route one query after the macro router has already selected Team mode."""
    normalized = str(query or "").strip()
    if not config.enabled or not normalized or normalized.startswith("/"):
        return None

    started = time.perf_counter()
    tokens = _tokens(normalized)
    complexity = _query_complexity(normalized, tokens)
    topology_scores = tuple(
        sorted(
            (
                _score_topology(normalized, tokens, complexity, item, config)
                for item in config.topologies
            ),
            key=lambda score: (-score.score, score.candidate_id),
        )
    )
    selected_score = topology_scores[0]
    fallback_reason = ""
    if selected_score.score < config.confidence_threshold:
        topology = _require_topology(config.topologies, config.default_topology)
        fallback_reason = "low_topology_confidence"
    else:
        topology = _require_topology(config.topologies, selected_score.candidate_id)

    role_scores = tuple(
        sorted(
            (_score_role(normalized, tokens, role) for role in config.roles),
            key=lambda score: (-score.score, score.candidate_id),
        )
    )
    selected_roles = [
        score.candidate_id
        for score in role_scores
        if score.score >= config.role_threshold
        and score.candidate_id != config.default_role
    ][: config.max_roles]
    if topology.enable_verification and "reviewer" in {
        role.role_id for role in config.roles
    }:
        selected_roles = _append_unique(selected_roles, "reviewer")
    if not selected_roles:
        selected_roles = [config.default_role]
    selected_roles = selected_roles[: config.max_roles]

    confidence = selected_score.score if not fallback_reason else selected_score.score
    return TeamTopologyDecision(
        topology=topology.topology_id,
        roles=tuple(selected_roles),
        confidence=max(0.0, min(1.0, confidence)),
        dispatch_mode=topology.dispatch_mode,
        enable_verification=topology.enable_verification,
        max_review_rounds=topology.max_review_rounds,
        reason=(
            f"topology={topology.topology_id}; "
            f"roles={','.join(selected_roles)}; complexity={complexity}"
        ),
        fallback_reason=fallback_reason,
        duration_ms=(time.perf_counter() - started) * 1000,
        topology_scores=topology_scores,
        role_scores=role_scores,
        features={
            "query_complexity": complexity,
            "query_token_count": len(tokens),
        },
    )


def _score_topology(
    query: str,
    tokens: set[str],
    complexity: int,
    option: TopologyOption,
    config: TeamRoutingConfig,
) -> RoutingScore:
    relevance = _semantic_relevance(
        query,
        tokens,
        (*option.routing_markers, option.description),
    )
    complexity_fit = 1.0 - abs(complexity - option.complexity) / 2.0
    complexity_fit = max(0.0, complexity_fit)
    cost_penalty = config.cost_weight * ((option.cost_tier - 1) / 2.0)
    score = 0.68 * relevance + 0.32 * complexity_fit - cost_penalty
    return RoutingScore(
        candidate_id=option.topology_id,
        score=max(0.0, min(1.0, score)),
        relevance=relevance,
        complexity_fit=complexity_fit,
        cost_penalty=cost_penalty,
    )


def _score_role(
    query: str,
    tokens: set[str],
    role: RoleOption,
) -> RoutingScore:
    relevance = _semantic_relevance(
        query,
        tokens,
        (*role.routing_markers, *role.capabilities, role.description),
    )
    score = max(0.0, min(1.0, relevance + role.priority))
    return RoutingScore(
        candidate_id=role.role_id,
        score=score,
        relevance=relevance,
    )


def _semantic_relevance(
    query: str,
    tokens: set[str],
    candidate_texts: Iterable[str],
) -> float:
    normalized_query = query.lower()
    texts = tuple(text.lower().strip() for text in candidate_texts if text)
    marker_hits = sum(1 for text in texts if text and text in normalized_query)
    marker_score = min(1.0, marker_hits / 2.0)
    candidate_tokens = _tokens(" ".join(texts))
    overlap = len(tokens & candidate_tokens)
    token_score = overlap / max(1.0, math.sqrt(len(candidate_tokens)))
    return min(1.0, 0.72 * marker_score + 0.28 * token_score)


def _query_complexity(query: str, tokens: set[str]) -> int:
    normalized = query.lower()
    score = 1
    if len(tokens) >= 18 or any(marker in normalized for marker in _COMPLEXITY_MARKERS):
        score += 1
    if len(tokens) >= 45 or normalized.count("?") > 1:
        score += 1
    return min(3, score)


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(value)}


def _require_topology(
    options: tuple[TopologyOption, ...],
    topology_id: str,
) -> TopologyOption:
    return next(option for option in options if option.topology_id == topology_id)


def _append_unique(values: list[str], value: str) -> list[str]:
    if value not in values:
        values.append(value)
    return values

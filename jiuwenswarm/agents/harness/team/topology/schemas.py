"""Contracts for query-adaptive routing inside Team mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TopologyOption:
    topology_id: str
    description: str
    dispatch_mode: str = "autonomous"
    routing_markers: tuple[str, ...] = ()
    complexity: int = 2
    cost_tier: int = 1
    enable_verification: bool = False
    max_review_rounds: int = 1


@dataclass(frozen=True)
class RoleOption:
    role_id: str
    description: str
    capabilities: tuple[str, ...] = ()
    routing_markers: tuple[str, ...] = ()
    priority: float = 0.0


@dataclass(frozen=True)
class TeamRoutingConfig:
    enabled: bool = False
    confidence_threshold: float = 0.45
    role_threshold: float = 0.16
    max_roles: int = 4
    default_topology: str = "sequential"
    default_role: str = "generalist"
    cost_weight: float = 0.08
    topologies: tuple[TopologyOption, ...] = ()
    roles: tuple[RoleOption, ...] = ()


@dataclass(frozen=True)
class RoutingScore:
    candidate_id: str
    score: float
    relevance: float
    complexity_fit: float = 0.0
    cost_penalty: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "score": round(self.score, 6),
            "relevance": round(self.relevance, 6),
            "complexity_fit": round(self.complexity_fit, 6),
            "cost_penalty": round(self.cost_penalty, 6),
        }


@dataclass(frozen=True)
class TeamTopologyDecision:
    """A topology decision followed by an ordered role allocation."""

    topology: str
    roles: tuple[str, ...]
    confidence: float
    dispatch_mode: str
    enable_verification: bool = False
    max_review_rounds: int = 1
    source: str = "rules"
    reason: str = ""
    fallback_reason: str = ""
    duration_ms: float = 0.0
    topology_scores: tuple[RoutingScore, ...] = ()
    role_scores: tuple[RoutingScore, ...] = ()
    features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topology": self.topology,
            "roles": list(self.roles),
            "confidence": round(self.confidence, 6),
            "dispatch_mode": self.dispatch_mode,
            "enable_verification": self.enable_verification,
            "max_review_rounds": self.max_review_rounds,
            "source": self.source,
            "reason": self.reason,
            "fallback_reason": self.fallback_reason,
            "duration_ms": round(self.duration_ms, 3),
            "topology_scores": [score.to_dict() for score in self.topology_scores],
            "role_scores": [score.to_dict() for score in self.role_scores],
            "features": dict(self.features),
        }

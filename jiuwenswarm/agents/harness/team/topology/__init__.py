"""Query-adaptive collaboration routing for Team mode only."""

from jiuwenswarm.agents.harness.team.topology.application import (
    apply_team_routing_to_spec,
    build_team_routing_prompt,
)
from jiuwenswarm.agents.harness.team.topology.config import (
    load_team_routing_config,
    team_routing_config_from_dict,
)
from jiuwenswarm.agents.harness.team.topology.router import route_team_query
from jiuwenswarm.agents.harness.team.topology.schemas import (
    RoleOption,
    RoutingScore,
    TeamRoutingConfig,
    TeamTopologyDecision,
    TopologyOption,
)

__all__ = [
    "RoleOption",
    "RoutingScore",
    "TeamRoutingConfig",
    "TeamTopologyDecision",
    "TopologyOption",
    "apply_team_routing_to_spec",
    "build_team_routing_prompt",
    "load_team_routing_config",
    "route_team_query",
    "team_routing_config_from_dict",
]

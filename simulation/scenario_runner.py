"""
SETMS — Digital Twin Scenario Runner (Milestone 10)
Executes end-to-end simulation scenarios in the fictional city of Navapur.
Evaluates route optimization, priority engine decisions, and travel time savings.

Usage:
  python -m simulation.scenario_runner --scenario conflict
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.algorithms.priority import (
    EmergencyPriorityEngine,
    AmbulanceApproachCandidate,
    PrioritySeverity,
)
from app.algorithms.routing import (
    RoadNetworkRouter,
    GraphNode,
    GraphEdge,
)
from app.algorithms.corridor import (
    SafeCorridorScheduler,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SETMS-ScenarioRunner")


def build_navapur_graph() -> RoadNetworkRouter:
    """Builds the 3x3 Navapur road network graph."""
    router = RoadNetworkRouter()

    # 9 Intersections
    nodes = [
        GraphNode("A1", "A1-North-West", 18.5250, 73.8520, True, "SIG-A1"),
        GraphNode("A2", "A2-North-Central", 18.5250, 73.8567, True, "SIG-A2"),
        GraphNode("A3", "A3-North-East", 18.5250, 73.8614, True, "SIG-A3"),
        GraphNode("B1", "B1-West", 18.5204, 73.8520, True, "SIG-B1"),
        GraphNode("B2", "B2-City Centre", 18.5204, 73.8567, True, "SIG-B2"),
        GraphNode("B3", "B3-East", 18.5204, 73.8614, True, "SIG-B3"),
        GraphNode("C1", "C1-South-West", 18.5158, 73.8520, True, "SIG-C1"),
        GraphNode("C2", "C2-South-Central", 18.5158, 73.8567, True, "SIG-C2"),
        GraphNode("C3", "C3-South-East", 18.5158, 73.8614, True, "SIG-C3"),
    ]
    for n in nodes:
        router.add_node(n)

    # Road Edges (Grid links)
    edges = [
        GraphEdge("e_A1_A2", "A1", "A2", "North Ave", 500.0, 50.0, 1.2),
        GraphEdge("e_A2_A3", "A2", "A3", "North Ave", 500.0, 50.0, 1.2),
        GraphEdge("e_B1_B2", "B1", "B2", "MG Road", 500.0, 50.0, 1.8),
        GraphEdge("e_B2_B3", "B2", "B3", "MG Road", 500.0, 50.0, 1.5),
        GraphEdge("e_C1_C2", "C1", "C2", "South Ring", 500.0, 50.0, 1.1),
        GraphEdge("e_C2_C3", "C2", "C3", "South Ring", 500.0, 50.0, 1.1),
        GraphEdge("e_A1_B1", "A1", "B1", "West Cross", 500.0, 45.0, 1.3),
        GraphEdge("e_B1_C1", "B1", "C1", "West Cross", 500.0, 45.0, 1.2),
        GraphEdge("e_A2_B2", "A2", "B2", "Central Spine", 500.0, 45.0, 2.0),
        GraphEdge("e_B2_C2", "B2", "C2", "Central Spine", 500.0, 45.0, 1.7),
        GraphEdge("e_A3_B3", "A3", "B3", "East Cross", 500.0, 45.0, 1.1),
        GraphEdge("e_B3_C3", "B3", "C3", "East Cross", 500.0, 45.0, 1.1),
    ]
    for e in edges:
        router.add_edge(e)

    return router


def run_scenario_conflict():
    logger.info("==================================================================")
    logger.info("RUNNING SCENARIO: TWO AMBULANCES APPROACHING INTERSECTION CONFLICT")
    logger.info("==================================================================")

    now = datetime.now(timezone.utc)
    router = build_navapur_graph()
    priority_engine = EmergencyPriorityEngine()
    corridor_scheduler = SafeCorridorScheduler()

    # Ambulance 1: AMB-Alpha (Critical, approaching SIG-B2 from West node B1)
    cand_alpha = AmbulanceApproachCandidate(
        ambulance_id="amb-alpha",
        call_sign="AMB-Alpha",
        severity=PrioritySeverity.CRITICAL,
        distance_to_intersection_meters=350.0,
        eta_to_intersection_seconds=42.0,
        requested_at=now - timedelta(minutes=2),
    )

    # Ambulance 2: AMB-Bravo (High, approaching SIG-B2 from North node A2)
    cand_bravo = AmbulanceApproachCandidate(
        ambulance_id="amb-bravo",
        call_sign="AMB-Bravo",
        severity=PrioritySeverity.HIGH,
        distance_to_intersection_meters=280.0,
        eta_to_intersection_seconds=36.0,
        requested_at=now - timedelta(seconds=45),
    )

    logger.info("Evaluating candidates at intersection SIG-B2 (City Centre):")
    ranked = priority_engine.rank_candidates([cand_alpha, cand_bravo], now)

    for res in ranked:
        logger.info(f"  Rank #{res.rank}: {res.explanation}")

    winner = ranked[0]
    loser = ranked[1]
    logger.info(f"\nDecision Result: {winner.call_sign} awarded green preemption at SIG-B2.")

    # Schedule Corridor for Winner
    route_alpha = router.find_fastest_route("B1", "B3")
    logger.info(f"Optimal Corridor Route for {winner.call_sign}: {' -> '.join(route_alpha.path_node_ids)}")
    logger.info(f"Total Corridor Distance: {route_alpha.total_distance_meters}m | Estimated Time: {route_alpha.total_duration_seconds:.1f}s")

    # Lock intersection for winner
    corridor_scheduler.acquire_lock("SIG-B2", "corr-alpha", winner.ambulance_id, "W-E")
    logger.info("SIG-B2 preemption lock acquired for West-East corridor.")

    # Check that conflicting approach for loser is correctly blocked
    conflict_check = corridor_scheduler.build_corridor_schedule(
        corridor_id="corr-bravo",
        emergency_id="emg-bravo",
        ambulance_id=loser.ambulance_id,
        signal_steps=[{"signal_id": "SIG-B2", "signal_name": "City Centre", "eta_offset_sec": 36.0, "approach_direction": "N-S"}],
    )

    assert conflict_check.conflict_detected is True
    logger.info(f"Safety verification: Conflict detected as expected: '{conflict_check.conflict_description}'")

    # Release lock after passage
    corridor_scheduler.release_all_for_corridor("corr-alpha")
    logger.info("AMB-Alpha cleared intersection. All signals safely restored to normal cycle.")
    logger.info("Scenario completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SETMS Scenario Runner")
    parser.add_argument("--scenario", default="conflict", choices=["conflict", "single"])
    args = parser.parse_args()

    run_scenario_conflict()

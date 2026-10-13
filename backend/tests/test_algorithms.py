"""
SETMS — Unit Tests for Safety Algorithms
Tests the Priority Engine, Road Network Router (Dijkstra/A*), and Safe Corridor Scheduler (Conflict Prevention).
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.algorithms.priority import (
    EmergencyPriorityEngine,
    AmbulanceApproachCandidate,
    PrioritySeverity,
)
from app.algorithms.routing import (
    RoadNetworkRouter,
    GraphNode,
    GraphEdge,
    haversine_distance,
)
from app.algorithms.corridor import (
    SafeCorridorScheduler,
    SignalPreemptionState,
)


def test_priority_engine_severity_ranking():
    """Higher medical severity must achieve higher priority score all else being equal."""
    engine = EmergencyPriorityEngine()
    now = datetime.now(timezone.utc)

    critical = AmbulanceApproachCandidate(
        ambulance_id="amb-1",
        call_sign="AMB-Alpha",
        severity=PrioritySeverity.CRITICAL,
        distance_to_intersection_meters=300.0,
        eta_to_intersection_seconds=60.0,
        requested_at=now,
    )

    high = AmbulanceApproachCandidate(
        ambulance_id="amb-2",
        call_sign="AMB-Bravo",
        severity=PrioritySeverity.HIGH,
        distance_to_intersection_meters=300.0,
        eta_to_intersection_seconds=60.0,
        requested_at=now,
    )

    normal = AmbulanceApproachCandidate(
        ambulance_id="amb-3",
        call_sign="AMB-Charlie",
        severity=PrioritySeverity.NORMAL,
        distance_to_intersection_meters=300.0,
        eta_to_intersection_seconds=60.0,
        requested_at=now,
    )

    ranked = engine.rank_candidates([normal, critical, high], now)
    assert ranked[0].ambulance_id == "amb-1"
    assert ranked[1].ambulance_id == "amb-2"
    assert ranked[2].ambulance_id == "amb-3"
    assert ranked[0].rank == 1
    assert ranked[0].total_score > ranked[1].total_score > ranked[2].total_score


def test_priority_engine_anti_starvation():
    """Ambulances waiting significantly longer accumulate anti-starvation bonus."""
    engine = EmergencyPriorityEngine()
    now = datetime.now(timezone.utc)

    # High severity requested just now
    fresh_high = AmbulanceApproachCandidate(
        ambulance_id="amb-fresh",
        call_sign="AMB-Fresh",
        severity=PrioritySeverity.HIGH,
        distance_to_intersection_meters=400.0,
        eta_to_intersection_seconds=90.0,
        requested_at=now,
    )

    # Normal severity requested 8 minutes ago (long wait)
    starving_normal = AmbulanceApproachCandidate(
        ambulance_id="amb-starving",
        call_sign="AMB-Starving",
        severity=PrioritySeverity.NORMAL,
        distance_to_intersection_meters=200.0,
        eta_to_intersection_seconds=40.0,
        requested_at=now - timedelta(minutes=8),
    )

    score_fresh = engine.calculate_score(fresh_high, now)
    score_starving = engine.calculate_score(starving_normal, now)

    assert score_starving.anti_starvation_component > score_fresh.anti_starvation_component


def test_road_network_router_fastest_path():
    """Dijkstra algorithm finds valid minimum travel time route through graph."""
    router = RoadNetworkRouter()

    # Create 3 collinear nodes A -> B -> C
    router.add_node(GraphNode(id="n1", name="Node 1", latitude=18.520, longitude=73.850, is_intersection=True, signal_id="sig-1"))
    router.add_node(GraphNode(id="n2", name="Node 2", latitude=18.525, longitude=73.855, is_intersection=True, signal_id="sig-2"))
    router.add_node(GraphNode(id="n3", name="Node 3", latitude=18.530, longitude=73.860, is_intersection=True, signal_id="sig-3"))

    router.add_edge(GraphEdge(id="e1", source_node_id="n1", target_node_id="n2", road_name="Main St", distance_meters=500.0, speed_limit_kmh=50.0))
    router.add_edge(GraphEdge(id="e2", source_node_id="n2", target_node_id="n3", road_name="Main St", distance_meters=500.0, speed_limit_kmh=50.0))

    route = router.find_fastest_route("n1", "n3")
    assert route is not None
    assert route.path_node_ids == ["n1", "n2", "n3"]
    assert route.path_signal_ids == ["sig-1", "sig-2", "sig-3"]
    assert route.total_distance_meters == 1000.0
    assert route.total_duration_seconds > 0


def test_corridor_scheduler_conflict_prevention():
    """Signal lock prevents conflicting green phases for competing corridors."""
    scheduler = SafeCorridorScheduler()

    # Ambulance A locks Signal 1 on North-South approach
    locked = scheduler.acquire_lock(
        signal_id="sig-1",
        corridor_id="corr-A",
        ambulance_id="amb-A",
        approach="N-S",
    )
    assert locked is True
    assert scheduler.is_signal_locked("sig-1") is True

    # Ambulance B plans corridor needing Signal 1 on East-West approach (CONFLICT)
    plan_b = scheduler.build_corridor_schedule(
        corridor_id="corr-B",
        emergency_id="emg-B",
        ambulance_id="amb-B",
        signal_steps=[{"signal_id": "sig-1", "signal_name": "Main Junction", "eta_offset_sec": 30.0, "approach_direction": "E-W"}],
    )

    assert plan_b.conflict_detected is True
    assert "already locked" in plan_b.conflict_description
    assert "conflicting approach" in plan_b.conflict_description

    # Release Ambulance A corridor
    released_count = scheduler.release_all_for_corridor("corr-A")
    assert released_count == 1
    assert scheduler.is_signal_locked("sig-1") is False

    # Now Ambulance B can safely acquire lock
    locked_b = scheduler.acquire_lock("sig-1", "corr-B", "amb-B", "E-W")
    assert locked_b is True

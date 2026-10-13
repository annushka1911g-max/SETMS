"""
SETMS — Priority Engine
Deterministic calculation of priority scores for emergency vehicles approaching intersections.

Formula:
  Score = (Severity_Weight * 0.40) + (Closeness_Weight * 0.25) +
          (ETA_Urgency * 0.20) + (Anti_Starvation_Bonus * 0.15)

Where:
  - Severity_Weight: CRITICAL=100, HIGH=65, NORMAL=35
  - Closeness_Weight: 100 * max(0, 1 - (distance_meters / max_detection_radius_meters))
  - ETA_Urgency: 100 * max(0, 1 - (eta_seconds / 300))
  - Anti_Starvation_Bonus: min(100, (wait_seconds / 60) * 20)

Note: This formula is an operational heuristic for simulation and traffic dispatch;
it is not a medically validated clinical score.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PrioritySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


SEVERITY_WEIGHTS = {
    PrioritySeverity.CRITICAL: 100.0,
    PrioritySeverity.HIGH: 65.0,
    PrioritySeverity.NORMAL: 35.0,
}


@dataclass
class AmbulanceApproachCandidate:
    ambulance_id: str
    call_sign: str
    severity: PrioritySeverity
    distance_to_intersection_meters: float
    eta_to_intersection_seconds: float
    requested_at: datetime
    active_corridor_id: Optional[str] = None
    has_active_corridor: bool = False
    vehicle_type: str = "ALS"


@dataclass
class PriorityEvaluationResult:
    ambulance_id: str
    call_sign: str
    total_score: float
    severity_component: float
    closeness_component: float
    eta_component: float
    anti_starvation_component: float
    has_active_corridor: bool
    rank: int
    explanation: str


class EmergencyPriorityEngine:
    """
    Deterministic priority scoring and conflict resolution for multiple
    approaching emergency vehicles at an intersection or along corridor paths.
    """

    def __init__(
        self,
        max_detection_radius_meters: float = 1000.0,
        max_eta_window_seconds: float = 300.0,
        weight_severity: float = 0.40,
        weight_closeness: float = 0.25,
        weight_eta: float = 0.20,
        weight_starvation: float = 0.15,
    ):
        self.max_detection_radius = max_detection_radius_meters
        self.max_eta_window = max_eta_window_seconds
        self.w_severity = weight_severity
        self.w_closeness = weight_closeness
        self.w_eta = weight_eta
        self.w_starvation = weight_starvation

    def calculate_score(
        self,
        candidate: AmbulanceApproachCandidate,
        now: Optional[datetime] = None,
    ) -> PriorityEvaluationResult:
        if now is None:
            now = datetime.now(timezone.utc)

        # 1. Severity weight
        sev_raw = SEVERITY_WEIGHTS.get(candidate.severity, 35.0)

        # 2. Closeness weight (closer to intersection yields higher urgency)
        closeness_ratio = max(0.0, 1.0 - (candidate.distance_to_intersection_meters / self.max_detection_radius))
        closeness_raw = closeness_ratio * 100.0

        # 3. ETA urgency (shorter ETA yields higher urgency)
        eta_ratio = max(0.0, 1.0 - (candidate.eta_to_intersection_seconds / self.max_eta_window))
        eta_raw = eta_ratio * 100.0

        # 4. Anti-starvation bonus (vehicles waiting longer accumulate score boost)
        req_time = candidate.requested_at
        if req_time.tzinfo is None:
            req_time = req_time.replace(tzinfo=timezone.utc)
        elapsed_seconds = max(0.0, (now - req_time).total_seconds())
        starvation_raw = min(100.0, (elapsed_seconds / 60.0) * 20.0)

        # 5. Composite score
        score = (
            (sev_raw * self.w_severity) +
            (closeness_raw * self.w_closeness) +
            (eta_raw * self.w_eta) +
            (starvation_raw * self.w_starvation)
        )

        # 6. Existing active corridor bonus to prevent flapping/oscillation
        if candidate.has_active_corridor:
            score += 15.0

        explanation = (
            f"Ambulance {candidate.call_sign} [{candidate.severity.value}] "
            f"score={score:.1f} (Severity: {sev_raw:.0f}w, Dist: {candidate.distance_to_intersection_meters:.0f}m, "
            f"ETA: {candidate.eta_to_intersection_seconds:.0f}s, Wait: {elapsed_seconds:.0f}s)"
        )

        return PriorityEvaluationResult(
            ambulance_id=candidate.ambulance_id,
            call_sign=candidate.call_sign,
            total_score=round(score, 2),
            severity_component=round(sev_raw * self.w_severity, 2),
            closeness_component=round(closeness_raw * self.w_closeness, 2),
            eta_component=round(eta_raw * self.w_eta, 2),
            anti_starvation_component=round(starvation_raw * self.w_starvation, 2),
            has_active_corridor=candidate.has_active_corridor,
            rank=1,
            explanation=explanation,
        )

    def rank_candidates(
        self,
        candidates: list[AmbulanceApproachCandidate],
        now: Optional[datetime] = None,
    ) -> list[PriorityEvaluationResult]:
        """
        Evaluate and rank multiple competing ambulances.
        Higher score wins. In case of exact tie, earlier requested_at wins.
        """
        if not candidates:
            return []

        results = [self.calculate_score(c, now) for c in candidates]

        # Tie-breaker: sort by score desc, then candidate request time
        cand_map = {c.ambulance_id: c for c in candidates}
        results.sort(
            key=lambda r: (
                r.total_score,
                -cand_map[r.ambulance_id].requested_at.timestamp()
            ),
            reverse=True,
        )

        for idx, res in enumerate(results, start=1):
            res.rank = idx

        return results

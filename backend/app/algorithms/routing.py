"""
SETMS — Road Network & Route Optimizer
Implements Dijkstra & A* pathfinding on the urban road graph with dynamic congestion weighting.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GraphNode:
    id: str
    name: str
    latitude: float
    longitude: float
    is_intersection: bool
    signal_id: Optional[str] = None


@dataclass
class GraphEdge:
    id: str
    source_node_id: str
    target_node_id: str
    road_name: str
    distance_meters: float
    speed_limit_kmh: float = 50.0
    congestion_multiplier: float = 1.0  # 1.0 = free flow, 2.5 = heavy traffic
    one_way: bool = False

    @property
    def travel_time_seconds(self) -> float:
        """Effective travel time considering speed limit and congestion."""
        speed_mps = max(1.0, (self.speed_limit_kmh * 1000.0 / 3600.0) / self.congestion_multiplier)
        return self.distance_meters / speed_mps


@dataclass
class RouteStep:
    node_id: str
    node_name: str
    latitude: float
    longitude: float
    is_intersection: bool
    signal_id: Optional[str]
    cumulative_distance_meters: float
    cumulative_duration_seconds: float
    estimated_arrival_offset_seconds: float


@dataclass
class OptimizedRoute:
    path_node_ids: list[str]
    path_signal_ids: list[str]
    steps: list[RouteStep]
    total_distance_meters: float
    total_duration_seconds: float
    origin_node_id: str
    destination_node_id: str


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula for distance in meters between two lat/lng points."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class RoadNetworkRouter:
    """
    Road network graph representing intersections, road links, and routing algorithms.
    """

    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.adjacency: dict[str, list[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source_node_id not in self.adjacency:
            self.adjacency[edge.source_node_id] = []
        self.adjacency[edge.source_node_id].append(edge)

        if not edge.one_way:
            # Add reverse edge
            rev = GraphEdge(
                id=f"{edge.id}_rev",
                source_node_id=edge.target_node_id,
                target_node_id=edge.source_node_id,
                road_name=edge.road_name,
                distance_meters=edge.distance_meters,
                speed_limit_kmh=edge.speed_limit_kmh,
                congestion_multiplier=edge.congestion_multiplier,
                one_way=False,
            )
            if edge.target_node_id not in self.adjacency:
                self.adjacency[edge.target_node_id] = []
            self.adjacency[edge.target_node_id].append(rev)

    def find_nearest_node(self, lat: float, lon: float) -> Optional[GraphNode]:
        """Find the nearest graph node to given coordinates."""
        if not self.nodes:
            return None
        return min(
            self.nodes.values(),
            key=lambda n: haversine_distance(lat, lon, n.latitude, n.longitude),
        )

    def find_fastest_route(
        self,
        origin_node_id: str,
        destination_node_id: str,
        emergency_speed_boost: float = 1.25,  # Ambulances travel ~25% faster when signals cleared
    ) -> Optional[OptimizedRoute]:
        """
        Calculates optimal route using Dijkstra's algorithm weighted by travel time.
        """
        if origin_node_id not in self.nodes or destination_node_id not in self.nodes:
            return None

        # distances stores (travel_time, distance_meters)
        times: dict[str, float] = {node_id: float("inf") for node_id in self.nodes}
        distances: dict[str, float] = {node_id: float("inf") for node_id in self.nodes}
        previous: dict[str, tuple[str, GraphEdge]] = {}  # target -> (source, edge)

        times[origin_node_id] = 0.0
        distances[origin_node_id] = 0.0

        # Priority queue stores (travel_time, node_id)
        pq: list[tuple[float, str]] = [(0.0, origin_node_id)]

        while pq:
            curr_time, curr_node_id = heapq.heappop(pq)

            if curr_time > times[curr_node_id]:
                continue

            if curr_node_id == destination_node_id:
                break

            for edge in self.adjacency.get(curr_node_id, []):
                # Apply emergency speed advantage
                edge_time = edge.travel_time_seconds / emergency_speed_boost
                new_time = curr_time + edge_time
                new_dist = distances[curr_node_id] + edge.distance_meters

                neighbor = edge.target_node_id
                if new_time < times.get(neighbor, float("inf")):
                    times[neighbor] = new_time
                    distances[neighbor] = new_dist
                    previous[neighbor] = (curr_node_id, edge)
                    heapq.heappush(pq, (new_time, neighbor))

        if times[destination_node_id] == float("inf"):
            return None  # No path exists

        # Reconstruct path
        path_nodes: list[str] = []
        curr = destination_node_id
        while curr in previous:
            path_nodes.append(curr)
            curr = previous[curr][0]
        path_nodes.append(origin_node_id)
        path_nodes.reverse()

        # Build detailed route steps with ETA progression
        steps: list[RouteStep] = []
        cum_dist = 0.0
        cum_time = 0.0
        path_signal_ids: list[str] = []

        for i, nid in enumerate(path_nodes):
            node = self.nodes[nid]
            if i > 0:
                prev_nid = path_nodes[i - 1]
                # Find edge
                for e in self.adjacency.get(prev_nid, []):
                    if e.target_node_id == nid:
                        cum_dist += e.distance_meters
                        cum_time += e.travel_time_seconds / emergency_speed_boost
                        break

            if node.signal_id and node.signal_id not in path_signal_ids:
                path_signal_ids.append(node.signal_id)

            steps.append(
                RouteStep(
                    node_id=node.id,
                    node_name=node.name,
                    latitude=node.latitude,
                    longitude=node.longitude,
                    is_intersection=node.is_intersection,
                    signal_id=node.signal_id,
                    cumulative_distance_meters=round(cum_dist, 1),
                    cumulative_duration_seconds=round(cum_time, 1),
                    estimated_arrival_offset_seconds=round(cum_time, 1),
                )
            )

        return OptimizedRoute(
            path_node_ids=path_nodes,
            path_signal_ids=path_signal_ids,
            steps=steps,
            total_distance_meters=round(cum_dist, 1),
            total_duration_seconds=round(cum_time, 1),
            origin_node_id=origin_node_id,
            destination_node_id=destination_node_id,
        )

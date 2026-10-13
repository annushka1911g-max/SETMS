"""
SETMS — Database Seed Script
Run: python -m scripts.seed
Creates demo accounts, ambulances, hospitals, signals, and road nodes for a fictional city.
Uses environment variables for seed credentials.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, create_tables
from app.models.ambulance import Ambulance
from app.models.device import Device
from app.models.enums import (
    AmbulanceStatus, DeviceConnectivity, DeviceType,
    SignalMode, SignalPhase, SignalStatus, UserRole,
)
from app.models.hospital import Hospital
from app.models.road import RoadEdge, RoadNode
from app.models.signal import TrafficSignal
from app.models.user import User


# ---------------------------------------------------------------------------
# Fictional City: "Navapur" — a small city in India (coordinates near Pune)
# ---------------------------------------------------------------------------
CITY_CENTER_LAT = 18.5204
CITY_CENTER_LNG = 73.8567

HOSPITALS_DATA = [
    {"name": "Navapur City Hospital", "address": "1 Hospital Road, Navapur",
     "latitude": 18.5250, "longitude": 73.8550, "emergency_bays_total": 8, "emergency_bays_available": 6},
    {"name": "St. Mary's Medical Centre", "address": "45 MG Road, Navapur",
     "latitude": 18.5180, "longitude": 73.8600, "emergency_bays_total": 5, "emergency_bays_available": 3},
    {"name": "Trauma Care Institute", "address": "12 Ring Road, Navapur",
     "latitude": 18.5120, "longitude": 73.8520, "emergency_bays_total": 10, "emergency_bays_available": 8},
]

AMBULANCES_DATA = [
    {"registration_number": "MH12-EMS-001", "call_sign": "AMB-Alpha", "vehicle_type": "ALS Type-A"},
    {"registration_number": "MH12-EMS-002", "call_sign": "AMB-Bravo", "vehicle_type": "ALS Type-A"},
    {"registration_number": "MH12-EMS-003", "call_sign": "AMB-Charlie", "vehicle_type": "BLS Type-B"},
    {"registration_number": "MH12-EMS-004", "call_sign": "AMB-Delta", "vehicle_type": "BLS Type-B"},
    {"registration_number": "MH12-EMS-005", "call_sign": "AMB-Echo", "vehicle_type": "ALS Type-A"},
]

# Road nodes define a small 3x3 grid for Navapur
NODES_DATA = [
    # Row A (north)
    {"name": "A1-North-West Intersection", "lat": 18.5250, "lng": 73.8520, "is_intersection": True},
    {"name": "A2-North-Central Intersection", "lat": 18.5250, "lng": 73.8567, "is_intersection": True},
    {"name": "A3-North-East Intersection", "lat": 18.5250, "lng": 73.8614, "is_intersection": True},
    # Row B (middle)
    {"name": "B1-West Intersection", "lat": 18.5204, "lng": 73.8520, "is_intersection": True},
    {"name": "B2-City Centre Intersection", "lat": 18.5204, "lng": 73.8567, "is_intersection": True},
    {"name": "B3-East Intersection", "lat": 18.5204, "lng": 73.8614, "is_intersection": True},
    # Row C (south)
    {"name": "C1-South-West Intersection", "lat": 18.5158, "lng": 73.8520, "is_intersection": True},
    {"name": "C2-South-Central Intersection", "lat": 18.5158, "lng": 73.8567, "is_intersection": True},
    {"name": "C3-South-East Intersection", "lat": 18.5158, "lng": 73.8614, "is_intersection": True},
    # Hospital waypoints
    {"name": "Navapur City Hospital Gate", "lat": 18.5250, "lng": 73.8550, "is_intersection": False},
    {"name": "St. Mary's Entrance", "lat": 18.5180, "lng": 73.8600, "is_intersection": False},
    {"name": "Trauma Care Entrance", "lat": 18.5120, "lng": 73.8520, "is_intersection": False},
]

SIGNALS_DATA = [
    {"name": "SIG-A1", "intersection_name": "North-West Intersection", "lat": 18.5250, "lng": 73.8520},
    {"name": "SIG-A2", "intersection_name": "North-Central Intersection", "lat": 18.5250, "lng": 73.8567},
    {"name": "SIG-A3", "intersection_name": "North-East Intersection", "lat": 18.5250, "lng": 73.8614},
    {"name": "SIG-B1", "intersection_name": "West Intersection", "lat": 18.5204, "lng": 73.8520},
    {"name": "SIG-B2", "intersection_name": "City Centre Intersection", "lat": 18.5204, "lng": 73.8567},
    {"name": "SIG-B3", "intersection_name": "East Intersection", "lat": 18.5204, "lng": 73.8614},
    {"name": "SIG-C1", "intersection_name": "South-West Intersection", "lat": 18.5158, "lng": 73.8520},
    {"name": "SIG-C2", "intersection_name": "South-Central Intersection", "lat": 18.5158, "lng": 73.8567},
    {"name": "SIG-C3", "intersection_name": "South-East Intersection", "lat": 18.5158, "lng": 73.8614},
]


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the straight-line distance between two GPS coordinates in meters."""
    import math
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def seed() -> None:
    settings = get_settings()
    await create_tables()

    async with AsyncSessionLocal() as db:
        # ---- Users ----
        users_seed = [
            (settings.seed_admin_email, "Admin User", UserRole.ADMIN, settings.seed_admin_password),
            (settings.seed_operator_email, "Traffic Operator", UserRole.TRAFFIC_OPERATOR, settings.seed_operator_password),
            (settings.seed_driver_email, "Ambulance Driver", UserRole.AMBULANCE_DRIVER, settings.seed_driver_password),
            (settings.seed_hospital_email, "Hospital Operator", UserRole.HOSPITAL_OPERATOR, settings.seed_hospital_password),
        ]

        created_users: dict[str, User] = {}
        for email, name, role, password in users_seed:
            from sqlalchemy import select
            existing = await db.execute(select(User).where(User.email == email))
            if not existing.scalar_one_or_none():
                user = User(
                    email=email, full_name=name, role=role,
                    hashed_password=hash_password(password),
                    is_active=True, is_verified=True,
                )
                db.add(user)
                await db.flush()
                created_users[role] = user
                print(f"  ✓ User created: {email} [{role}]")
            else:
                print(f"  ↺ User exists: {email}")

        # ---- Hospitals ----
        hospital_ids: list[str] = []
        for h in HOSPITALS_DATA:
            from sqlalchemy import select
            existing = await db.execute(select(Hospital).where(Hospital.name == h["name"]))
            if not existing.scalar_one_or_none():
                hospital = Hospital(
                    name=h["name"], address=h["address"],
                    latitude=h["latitude"], longitude=h["longitude"],
                    emergency_bays_total=h["emergency_bays_total"],
                    emergency_bays_available=h["emergency_bays_available"],
                    is_ready=True, is_active=True,
                )
                db.add(hospital)
                await db.flush()
                hospital_ids.append(hospital.id)
                print(f"  ✓ Hospital: {h['name']}")
            else:
                result = await db.execute(select(Hospital).where(Hospital.name == h["name"]))
                hospital_ids.append(result.scalar_one().id)
                print(f"  ↺ Hospital exists: {h['name']}")

        # ---- Ambulances ----
        for a in AMBULANCES_DATA:
            from sqlalchemy import select
            existing = await db.execute(select(Ambulance).where(
                Ambulance.registration_number == a["registration_number"]
            ))
            if not existing.scalar_one_or_none():
                ambulance = Ambulance(
                    registration_number=a["registration_number"],
                    call_sign=a["call_sign"],
                    vehicle_type=a["vehicle_type"],
                    status=AmbulanceStatus.AVAILABLE,
                    current_lat=CITY_CENTER_LAT + (hash(a["call_sign"]) % 100) * 0.0001,
                    current_lng=CITY_CENTER_LNG + (hash(a["call_sign"]) % 100) * 0.0001,
                    location_updated_at=datetime.now(timezone.utc),
                    is_active=True,
                )
                db.add(ambulance)
                await db.flush()
                print(f"  ✓ Ambulance: {a['call_sign']}")
            else:
                print(f"  ↺ Ambulance exists: {a['registration_number']}")

        # ---- Road Nodes ----
        node_ids: list[str] = []
        for n in NODES_DATA:
            from sqlalchemy import select
            existing = await db.execute(select(RoadNode).where(RoadNode.name == n["name"]))
            if not existing.scalar_one_or_none():
                node = RoadNode(
                    name=n["name"], latitude=n["lat"], longitude=n["lng"],
                    is_intersection=n["is_intersection"],
                )
                db.add(node)
                await db.flush()
                node_ids.append(node.id)
            else:
                result = await db.execute(select(RoadNode).where(RoadNode.name == n["name"]))
                node_ids.append(result.scalar_one().id)

        print(f"  ✓ {len(NODES_DATA)} road nodes seeded")

        # Build edges for 3x3 grid (bidirectional roads)
        # Grid indices: 0..8 = A1,A2,A3,B1,B2,B3,C1,C2,C3
        grid_connections = [
            (0, 1), (1, 2),        # Row A horizontal
            (3, 4), (4, 5),        # Row B horizontal
            (6, 7), (7, 8),        # Row C horizontal
            (0, 3), (3, 6),        # Column 1 vertical
            (1, 4), (4, 7),        # Column 2 vertical
            (2, 5), (5, 8),        # Column 3 vertical
        ]

        from sqlalchemy import func as sqlfunc
        edge_count = await db.scalar(select(sqlfunc.count(RoadEdge.id)))
        if edge_count == 0:
            for from_idx, to_idx in grid_connections:
                if from_idx >= len(node_ids) or to_idx >= len(node_ids):
                    continue
                from_id = node_ids[from_idx]
                to_id = node_ids[to_idx]
                from_node = NODES_DATA[from_idx]
                to_node = NODES_DATA[to_idx]
                dist = _haversine_meters(from_node["lat"], from_node["lng"],
                                          to_node["lat"], to_node["lng"])
                # Forward edge
                db.add(RoadEdge(from_node_id=from_id, to_node_id=to_id,
                                 distance_meters=dist, speed_limit_kmh=50.0,
                                 road_name=f"Road {from_idx}-{to_idx}"))
                # Reverse edge (bidirectional)
                db.add(RoadEdge(from_node_id=to_id, to_node_id=from_id,
                                 distance_meters=dist, speed_limit_kmh=50.0,
                                 road_name=f"Road {to_idx}-{from_idx}"))
            await db.flush()
            print(f"  ✓ Road edges created")

        # ---- Traffic Signals ----
        for s in SIGNALS_DATA:
            from sqlalchemy import select
            existing = await db.execute(select(TrafficSignal).where(TrafficSignal.name == s["name"]))
            if not existing.scalar_one_or_none():
                signal = TrafficSignal(
                    name=s["name"], intersection_name=s["intersection_name"],
                    latitude=s["lat"], longitude=s["lng"],
                    status=SignalStatus.OPERATIONAL,
                    current_phase=SignalPhase.RED,
                    current_mode=SignalMode.NORMAL,
                    is_active=True,
                )
                db.add(signal)
                await db.flush()

                # Create a simulator device for this signal
                device = Device(
                    name=f"SIM-{s['name']}",
                    device_type=DeviceType.SIMULATOR,
                    mqtt_client_id=f"sim-{s['name'].lower()}",
                    connectivity=DeviceConnectivity.ONLINE,
                    is_simulated=True,
                    is_active=True,
                    last_seen_at=datetime.now(timezone.utc),
                )
                db.add(device)
                await db.flush()
                signal.device_id = device.id
                await db.flush()

                print(f"  ✓ Signal: {s['name']}")
            else:
                print(f"  ↺ Signal exists: {s['name']}")

        await db.commit()
        print("\n✅ Seed complete! Demo credentials:")
        print(f"  Admin:    {settings.seed_admin_email} / {settings.seed_admin_password}")
        print(f"  Operator: {settings.seed_operator_email} / {settings.seed_operator_password}")
        print(f"  Driver:   {settings.seed_driver_email} / {settings.seed_driver_password}")
        print(f"  Hospital: {settings.seed_hospital_email} / {settings.seed_hospital_password}")


if __name__ == "__main__":
    print("🌱 Seeding SETMS database...")
    asyncio.run(seed())

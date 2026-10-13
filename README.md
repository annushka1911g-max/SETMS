# SETMS — Smart Emergency Traffic Management System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Language-Python%203.12-3776AB.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Saving Lives Through Intelligent Traffic Management.**  
> A complete, professional, end-to-end Smart Emergency Traffic Management System (SETMS) built for the Smart India Hackathon (SIH), academic evaluation, and urban traffic research.

---

## 🚦 Problem Statement & Solution

### The Problem
Ambulances lose critical minutes in congested urban intersections during the "Golden Hour". Conventional traffic signals operate on static timers or basic loop detectors that:
1. Do not coordinate with approaching emergency vehicles.
2. Cannot dynamically plan green corridors across sequential intersections.
3. Lack integration between emergency response dispatchers, traffic police, and destination hospitals.

### The SETMS Solution
SETMS provides an intelligent urban traffic orchestration platform featuring:
- **Dynamic Green Corridor Engine**: Plans and clears conflict-free corridors along optimized routes.
- **Priority & Conflict Management**: Automatically detects intersection conflicts between multiple responding emergency vehicles.
- **Computer Vision Density Estimation**: YOLO and OpenCV based vehicle detection with traffic density estimation and emergency vehicle candidate identification.
- **Hospital Coordination**: Live notification of incoming patients with estimated time of arrival (ETA), severity level, and automatic bay reservation tracking.
- **Hardware-in-the-Loop Simulation**: MQTT-connected IoT adapter supporting simulated signals and physical ESP32 miniature intersection models.
- **Simulated City Digital Twin**: Pre-configured with "Navapur", an urban test city with a connected road network, hospitals, intersections, and active ambulance units.

---

## 🏛️ System Architecture

```
                       +----------------------------------+
                       |          React Frontend          |
                       | (TypeScript + Vite + Tailwind)   |
                       +-----------------+----------------+
                                         |
                            HTTP / REST  |  Socket.IO / WS
                                         v
                       +----------------------------------+
                       |      FastAPI Backend Engine      |
                       |    - Route Optimization (A*)     |
                       |    - Corridor Conflict Resolver  |
                       |    - Role-Based Access Control   |
                       +--------+----------------+--------+
                                |                |
                  Internal HTTP |                | MQTT / PubSub
                                v                v
         +------------------------+    +-----------------------+
         |   AI Detection Engine  |    |     Mosquitto MQTT    |
         | (YOLOv8 + OpenCV Fall) |    |  (IoT / ESP32 Nodes)  |
         +------------------------+    +-----------------------+
                                \                /
                                 v              v
                       +----------------------------------+
                       |    PostgreSQL / SQLite Storage   |
                       |   + Redis Event State Caching    |
                       +----------------------------------+
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: v18+ (v20+ recommended)
- **Docker & Docker Compose** (optional for containerized deployment)

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-org/SETMS.git
cd SETMS
cp .env.example .env
```

### 2. Install Dependencies
```bash
# Set up Python virtual environment and install backend requirements
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Seed Database with Navapur City
```bash
# Seeds road graph, 9 signals, 5 ambulances, 3 hospitals, and demo users
source .venv/bin/activate
cd backend && python -m scripts.seed && cd ..
```

### 4. Run the Stack Locally
```bash
# Terminal 1: Backend
source .venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3 (Optional): AI Engine
source .venv/bin/activate
cd ai-engine
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Open `http://localhost:5173` in your browser.

---

## 🔑 Demo Accounts & Role Matrix

The seed script creates accounts with role-based permissions:

| Role | Email | Password | Access Rights |
|:---|:---|:---|:---|
| **Admin** | `admin@setms.org` | `Admin1234!` | Full system management, user administration, audits |
| **Traffic Operator** | `operator@setms.org` | `Operator1234!` | Approve/cancel green corridors, manual signal override |
| **Driver / Paramedic** | `driver@setms.org` | `Driver1234!` | Create emergency requests, transmit live telemetry |
| **Hospital Staff** | `hospital@setms.org` | `Hospital1234!` | View incoming ambulances, toggle bay availability |
| **Viewer** | `viewer@setms.org` | `Viewer1234!` | Read-only access to dashboard and analytics |

---

## 🧪 Testing & Validation

Run the automated test suite covering authentication, RBAC, health endpoints, and database models:

```bash
# Run backend pytest suite
source .venv/bin/activate
cd backend
pytest tests/ -v

# Run frontend build and typecheck
cd frontend
npm run build
```

---

## 📡 API Reference Overview

The backend provides interactive OpenAPI documentation at `http://localhost:8000/docs`:

- `POST /api/v1/auth/login` — Authenticate and receive JWT access token.
- `GET  /api/v1/dashboard/summary` — Real-time metrics (active emergencies, ambulances, signals, hospitals).
- `GET  /api/v1/emergencies` — List emergency incidents with pagination & filtering.
- `POST /api/v1/emergencies` — Create new emergency with triage priority.
- `POST /api/v1/corridors/plan` — Generate optimized corridor through road graph.
- `POST /api/v1/corridors/{id}/approve` — Operator approval with signal preemption lock.
- `POST /api/v1/corridors/{id}/cancel` — Release signals back to normal operational cycles.
- `GET  /api/v1/signals` — Real-time status and phase (RED / YELLOW / GREEN) of intersections.
- `POST /api/v1/signals/{id}/override` — Manual emergency override (restricted to operators).
- `GET  /api/v1/hospitals` — Hospital ER bed counts and incoming ambulance tracking.
- `POST /api/v1/ai/detect` — YOLO vehicle detection & density inference.

---

## 🔒 Safety & Failsafe Guarantees

1. **No Real Hardware Interference**: All traffic signals and actuators in this repository operate strictly in simulation or dedicated laboratory IoT bench environments.
2. **Conflict Prevention Engine**: Corridors cannot grant simultaneous green lights to conflicting intersection approaches.
3. **Emergency Override Timeout**: Any manual or emergency override automatically reverts to standard cycle after a configurable timeout (default 180s) if connection is lost.
4. **Audit Trail**: Every clearance request, approval, and phase transition is written to an immutable `audit_logs` table.

---

## 📜 License
This project is open-source under the MIT License.

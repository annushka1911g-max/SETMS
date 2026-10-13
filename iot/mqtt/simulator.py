"""
SETMS — MQTT Simulated Traffic Signal Adapter (Milestone 9)
Simulates 9 virtual IoT traffic light nodes in Navapur.
Subscribes to signal preemption topics and publishes simulated heartbeats.

Usage:
  python -m iot.mqtt.simulator
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    HAVE_PAHO = True
except ImportError:
    HAVE_PAHO = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SETMS-MQTT-Sim")

SIGNAL_IDS = [
    "SIG-A1", "SIG-A2", "SIG-A3",
    "SIG-B1", "SIG-B2", "SIG-B3",
    "SIG-C1", "SIG-C2", "SIG-C3",
]


class SimulatedSignalNode:
    def __init__(self, signal_id: str):
        self.signal_id = signal_id
        self.device_id = f"sim-{signal_id.lower()}"
        self.current_phase = "RED"
        self.last_heartbeat = time.time()

    def set_phase(self, phase: str) -> None:
        self.current_phase = phase
        logger.info(f"[{self.signal_id}] State changed to {phase} (Simulated Light Actuated)")


class MqttSimulatorService:
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.signals = {sid: SimulatedSignalNode(sid) for sid in SIGNAL_IDS}
        self.client: Optional[object] = None

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to Mosquitto broker (rc={rc})")
        for sid in self.signals:
            topic = f"setms/signals/{sid}/phase"
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            # Extract signal ID
            parts = topic.split("/")
            if len(parts) >= 3:
                sig_id = parts[2]
                if sig_id in self.signals:
                    self.signals[sig_id].set_phase(payload)
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def run_standalone(self, duration_seconds: int = 60) -> None:
        """Run simulated signal loop with simulated heartbeats."""
        logger.info("Starting SETMS Simulated Traffic Signal Nodes for Navapur...")
        logger.info(f"Initialized {len(self.signals)} virtual intersection controllers.")

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            now = time.time()
            for sid, node in self.signals.items():
                if now - node.last_heartbeat > 10.0:
                    node.last_heartbeat = now
                    logger.debug(f"Heartbeat: {node.device_id} status=ONLINE phase={node.current_phase}")

            time.sleep(1.0)

        logger.info("Simulated MQTT run completed.")


if __name__ == "__main__":
    service = MqttSimulatorService()
    service.run_standalone(duration_seconds=30)

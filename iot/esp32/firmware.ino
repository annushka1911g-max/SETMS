/*
 * SETMS — ESP32 Miniature Traffic Signal Firmware (Milestone 9)
 * Connects to local WiFi and Mosquitto MQTT broker.
 * Controls 3-state intersection LED lights (Red, Yellow, Green).
 *
 * Safety Invariant:
 * Includes hardcoded failsafe timeout. If broker communication is lost for
 * > 30 seconds, enters blinking YELLOW cautionary failsafe mode.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi Configuration (Configure for local demo router)
const char* WIFI_SSID     = "SETMS-Demo-AP";
const char* WIFI_PASSWORD = "EmergencyTraffic2026";

// MQTT Broker Configuration
const char* MQTT_BROKER   = "192.168.1.100"; // IP of SETMS backend host
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "setms_device";
const char* MQTT_PASS     = "device_secret";

// Device & Signal Identifier
const char* DEVICE_ID     = "esp32-sig-b2";
const char* SIGNAL_ID     = "SIG-B2";

// Hardware GPIO Pin Mapping (Miniature Traffic Light Module)
const int PIN_LED_RED     = 25;
const int PIN_LED_YELLOW  = 26;
const int PIN_LED_GREEN   = 27;

// Topics
const char* TOPIC_PHASE_CMD  = "setms/signals/SIG-B2/phase";
const char* TOPIC_HEARTBEAT  = "setms/devices/esp32-sig-b2/heartbeat";
const char* TOPIC_STATUS     = "setms/devices/esp32-sig-b2/status";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Failsafe tracking
unsigned long lastCommandTime = 0;
const unsigned long FAILSAFE_TIMEOUT_MS = 30000; // 30 seconds
bool failsafeActive = false;

enum SignalState {
  STATE_RED,
  STATE_YELLOW,
  STATE_GREEN,
  STATE_FAILSAFE_BLINK
};

SignalState currentState = STATE_RED;

void setLEDs(bool red, bool yellow, bool green) {
  digitalWrite(PIN_LED_RED, red ? HIGH : LOW);
  digitalWrite(PIN_LED_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_LED_GREEN, green ? HIGH : LOW);
}

void applyState(SignalState state) {
  currentState = state;
  switch (state) {
    case STATE_RED:
      setLEDs(true, false, false);
      break;
    case STATE_YELLOW:
      setLEDs(false, true, false);
      break;
    case STATE_GREEN:
      setLEDs(false, false, true);
      break;
    case STATE_FAILSAFE_BLINK:
      // Handled in main loop
      break;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char message[256];
  if (length >= sizeof(message)) return;
  memcpy(message, payload, length);
  message[length] = '\0';

  Serial.print("[MQTT RX] Topic: ");
  Serial.print(topic);
  Serial.print(" Payload: ");
  Serial.println(message);

  lastCommandTime = millis();
  failsafeActive = false;

  // Parse command (JSON or plain text phase)
  if (strstr(message, "GREEN") != NULL) {
    applyState(STATE_GREEN);
    Serial.println("-> Signal state set to GREEN (Corridor Preemption)");
  } else if (strstr(message, "YELLOW") != NULL) {
    applyState(STATE_YELLOW);
    Serial.println("-> Signal state set to YELLOW (Clearance Interval)");
  } else if (strstr(message, "RED") != NULL) {
    applyState(STATE_RED);
    Serial.println("-> Signal state set to RED (Normal Stop)");
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi connection timed out. Entering offline failsafe.");
  }
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker...");
    if (mqttClient.connect(DEVICE_ID, MQTT_USER, MQTT_PASS, TOPIC_STATUS, 1, true, "{\"status\":\"offline\"}")) {
      Serial.println("connected!");
      mqttClient.subscribe(TOPIC_PHASE_CMD);
      mqttClient.publish(TOPIC_STATUS, "{\"status\":\"online\",\"signal_id\":\"SIG-B2\"}", true);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 3 seconds...");
      delay(3000);
      break; // Non-blocking loop iteration
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);

  // Initial state: Red
  applyState(STATE_RED);

  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  lastCommandTime = millis();
}

unsigned long lastHeartbeat = 0;
unsigned long lastBlinkToggle = 0;
bool blinkState = false;

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqttClient.connected()) {
      connectMQTT();
    }
    mqttClient.loop();
  }

  // Check Failsafe Timeout
  if (millis() - lastCommandTime > FAILSAFE_TIMEOUT_MS) {
    if (!failsafeActive) {
      failsafeActive = true;
      Serial.println("⚠️ FAILSAFE ACTIVATED: Broker heartbeat timed out! Blinking cautionary yellow.");
    }
    // Blink yellow every 500ms
    if (millis() - lastBlinkToggle > 500) {
      lastBlinkToggle = millis();
      blinkState = !blinkState;
      setLEDs(false, blinkState, false);
    }
  }

  // Periodic Telemetry Heartbeat (every 10 seconds)
  if (millis() - lastHeartbeat > 10000 && mqttClient.connected()) {
    lastHeartbeat = millis();
    char hbPayload[128];
    snprintf(hbPayload, sizeof(hbPayload),
      "{\"device_id\":\"%s\",\"signal_id\":\"%s\",\"uptime_s\":%lu,\"rssi\":%d}",
      DEVICE_ID, SIGNAL_ID, millis() / 1000, WiFi.RSSI()
    );
    mqttClient.publish(TOPIC_HEARTBEAT, hbPayload);
  }
}

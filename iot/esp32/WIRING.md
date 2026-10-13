# SETMS — ESP32 Traffic Light Module Wiring Guide

> Hardware-in-the-Loop Integration (Milestone 9)  
> Suitable for Smart India Hackathon (SIH) bench hardware demonstration.

---

## 🧰 Required Components

| Item | Specification | Quantity |
|:---|:---|:---:|
| **Microcontroller** | ESP32 NodeMCU (ESP-WROOM-32) | 1 |
| **LED Traffic Module** | 3-state traffic light module (Red, Yellow, Green common-cathode) | 1 |
| **Resistors** | 220Ω (if using raw 5mm LEDs instead of PCB module) | 3 |
| **Jumper Wires** | Female-to-Male or Male-to-Male | 4 |
| **Breadboard** | Half-size standard solderless breadboard | 1 |
| **Power Supply** | Micro-USB cable connected to 5V 1A power adapter / laptop | 1 |

---

## 🔌 Pin Mapping Table

| LED Function | ESP32 GPIO Pin | Wire Color Recommendation | Notes |
|:---|:---:|:---:|:---|
| **Red Light** | `GPIO 25` | Red | Stop phase |
| **Yellow Light** | `GPIO 26` | Yellow | Clearance / Failsafe blink phase |
| **Green Light** | `GPIO 27` | Green | Preemption green corridor phase |
| **Common Cathode** | `GND` | Black | Ground reference |

---

## ⚡ Circuit Schematic

```
               ESP32 NodeMCU
           +-------------------+
           |                   |
           |     GPIO 25 [RED] +----[ 220Ω ]----+ (Anode) Red LED
           |                   |                          |
           |  GPIO 26 [YELLOW] +----[ 220Ω ]----+ (Anode) Yellow LED
           |                   |                          |
           |   GPIO 27 [GREEN] +----[ 220Ω ]----+ (Anode) Green LED
           |                   |                          |
           |               GND +--------------------------+ (Cathode Common)
           |                   |
           +-------------------+
```

*(Note: If using standard pre-assembled 4-pin 5V Traffic Light modules with built-in SMD resistors, pins are labeled `R`, `Y`, `G`, and `GND`. Simply connect directly without external resistors).*

---

## 🛠️ Step-by-Step Assembly Instructions

1. **Mount ESP32**: Insert ESP32 onto breadboard straddling the center divider.
2. **Connect Ground**: Run a black jumper wire from ESP32 `GND` pin to module `GND` pin.
3. **Connect Red LED**: Run a red jumper wire from `GPIO 25` to the `R` pin of the traffic light module.
4. **Connect Yellow LED**: Run a yellow jumper wire from `GPIO 26` to the `Y` pin of the traffic light module.
5. **Connect Green LED**: Run a green jumper wire from `GPIO 27` to the `G` pin of the traffic light module.
6. **Upload Firmware**: Open `iot/esp32/firmware.ino` in Arduino IDE, select board `DOIT ESP32 DEVKIT V1`, configure WiFi and MQTT IP, and click **Upload**.

---

## 🚨 Failsafe Behavior Demonstration

The firmware includes an automatic failsafe testable during evaluation:
1. When normal commands are received, the LED shows current phase (`RED`, `YELLOW`, or `GREEN`).
2. If the MQTT broker or network disconnects for **30 seconds**, the ESP32 automatically enters **cautionary flashing yellow** mode (500ms cycle).
3. As soon as connectivity is restored, the ESP32 resumes active corridor command execution.

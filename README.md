# ugv01-x3-obstacle-avoidance
Simple floor-color + edge based obstacle avoidance for Waveshare UGV01-X3 (RPi 5 + ESP32 + Pi Camera)

Simple autonomous obstacle avoidance based on floor color difference and edge detection  
for **Waveshare UGV01-X3** tracked robot chassis.

Runs on **Raspberry Pi 5** + **ESP32-WROOM** (General Driver for Robots firmware) + **Raspberry Pi Camera**.

## Project Description

The robot:
- Calibrates floor color (slow forward movement ~1.4 seconds)
- Analyzes the lower part of the camera frame (HSV difference from calibrated floor + Canny edges)
- Drives forward at medium speed
- Stops and turns when detecting obstacles, edges, or dark areas
- Includes corner escape mode (micro-turns + backward movement)

Control is done via UART (`/dev/ttyAMA0`, 115200 baud) using the same JSON commands as in the official web interface:  
**UGV01_BASE_WEB** → http://192.168.4.1 (AP mode) or local IP in STA mode.

## Hardware Requirements

- Waveshare **UGV01-X3** tracked chassis (with suspension)
- **Raspberry Pi 5** (installed as the upper computer)
- **ESP32-WROOM-32** (lower controller with General Driver for Robots firmware)
- **Raspberry Pi Camera Module** (CSI connection, fixed forward-facing — mandatory!)
- 3×18650 battery pack (or external power)
- UART connection: Raspberry Pi GPIO UART → ESP32 (usually `/dev/ttyAMA0`)

**Important about the camera**:  
The camera must be mounted **front-facing and looking forward** (not downward or upward).  
If you have a pan-tilt gimbal with bus servos — this script does **not** control it (can be added later).

## Preparation (one-time setup on Raspberry Pi)

1. Install **Raspberry Pi OS Bookworm 64-bit** (Desktop or Lite recommended).
2. Enable UART and camera:
   sudo raspi-config
   - Interface Options  
- Serial Port → No (login shell) → Yes (hardware port)  
- Camera → Enable  
- Finish → Reboot

3. Update system: sudo apt update && sudo apt upgrade -y
   
## Library Installation

Run these commands in order:

```bash
# 1. Install system packages (recommended for compatibility with Pi Camera & OpenCV)
sudo apt update
sudo apt install -y \
 python3-picamera2 \
 python3-opencv \
 python3-numpy \
 python3-serial

# 2. Install the only pip package needed
pip3 install pyserial

# ugv01-obstacle-avoidance

Simple floor-color + edge based obstacle avoidance for Waveshare UGV01 (RPi 5 + ESP32 + Pi Camera)

This repo contains a small Python script that lets the UGV01 drive around autonomously using only a single Pi Camera.
It detects “not floor” areas and edges in the lower part of the image, then stops/turns to avoid obstacles.

Control commands are sent from Raspberry Pi to the ESP32 over UART (`/dev/ttyAMA0`, `115200` baud).
The JSON format is the same one used by the official UGV01 web control page (UGV01_BASE_WEB).

## Hardware photo

![UGV01 robot setup](media/robot_ugv01.jpg)

## How the robot works

At startup the script calibrates the floor color: the robot moves forward slowly for ~1.4 seconds and takes ~35 HSV samples from a small patch near the bottom-center of the frame. The average HSV becomes the “floor reference”, so it adapts to your lighting and surface.

Then it runs a loop:
- looks at a bottom ROI (region of interest)
- compares HSV in center/side zones against the calibrated floor
- counts edges using Canny
- if it sees something “not like the floor” (or too many edges) it stops and turns
- if it gets stuck in a corner it switches to a simple escape mode (small turns + occasional reverse)

## Hardware

- Waveshare UGV01 tracked chassis
- Raspberry Pi 5
- ESP32-WROOM-32 running General Driver for Robots firmware
- Raspberry Pi CSI Camera mounted on the front, looking straight forward
- Power (3×18650 or external)
- UART wiring between Pi GPIO and ESP32 (typically `/dev/ttyAMA0`)

Camera note: it has to point forward. If you have a pan-tilt mount with servos — this script doesn’t control servos.

## One-time setup on Raspberry Pi

Install Raspberry Pi OS Bookworm 64-bit (Desktop or Lite).

Open raspi-config:

```bash
sudo raspi-config
```

Go to **Interface Options** and set two things:
- **Serial Port**: disable login shell over serial, enable hardware serial port
- **Camera**: enable camera interface

Reboot:

```bash
sudo reboot
```

Update system packages:

```bash
sudo apt update && sudo apt upgrade -y
```

Install recommended packages (best way on Raspberry Pi for camera + OpenCV):

```bash
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-serial
```

## Quick Start

```bash
git clone https://github.com/tetotetodouga/ugv01-obstacle-avoidance.git
cd ugv01-obstacle-avoidance
python3 avoid_obstacle.py
```

## Calibration & Tuning

If the robot detects obstacles too often (false positives) or too rarely (misses obstacles), tune the ROI and thresholds in `avoid_obstacle.py`.

### Floor calibration (HSV)

On startup, the robot performs an automatic floor calibration:
- Captures ~35 HSV samples from a small center patch
- Slowly drives forward for ~1.4 seconds during sampling
- Uses the average HSV as the “floor color” reference

### ROI (Region of Interest)

Obstacle detection is done in the lower part of the frame:

```python
y0 = int(h * 0.78)  # ROI top (default: 78% of frame height)
y1 = int(h * 0.95)  # ROI bottom (default: 95% of frame height)
```

If low obstacles are missed, lower `y0` (e.g. `0.70–0.75`).
If there are many false positives from the floor, raise `y0` (e.g. `0.82–0.85`).

### Floor calibration patch

HSV patch used for floor calibration:

```python
patch = hsv[int(h * 0.90):int(h * 0.95), int(w * 0.46):int(w * 0.54)]
```

You can narrow/widen this patch if the floor is reflective, patterned, or non-uniform.

### Detection thresholds

Main sensitivity parameters:
- `DIFF_THR_CENTER = 25.0` (HSV difference threshold, center)
- `DIFF_THR_SIDE = 25.0` (HSV difference threshold, sides)
- `EDGE_THR_CENTER = 1800` (Canny edge count threshold, center)
- `EDGE_THR_SIDE = 1400` (Canny edge count threshold, sides)

If detection is too sensitive, increase thresholds slightly.
If the robot misses obstacles, decrease thresholds slightly.

## UART check (recommended)

After reboot, confirm the UART device exists and permissions are OK.

Check your groups:

```bash
groups
```

Check serial devices:

```bash
ls -l /dev/ttyAMA0
ls -l /dev/serial0
```

If UART is set up correctly, at least one of these devices should exist and be accessible.

## Troubleshooting

### Camera

If `rpicam-hello` does not start:
- check that the camera is connected
- reseat the ribbon cable (orientation matters)
- make sure Camera is enabled in `raspi-config`
- reboot

If the image works but Python can’t access the camera:
- install picamera2

```bash
sudo apt install -y python3-picamera2
```

Also make sure the camera is not used by another program (only one process can use it).

### Python errors

If you see `ModuleNotFoundError`, install the missing dependency:

```bash
sudo apt install -y python3-<package-name>
```

If you see `Permission denied` when opening UART, add your user to `dialout` and reboot:

```bash
sudo usermod -a -G dialout $USER
sudo reboot
```

### Robot ignores commands (UART)

Common causes:
- no permissions (`dialout`)
- serial console over UART is still enabled
- wrong port selected (`/dev/ttyAMA0` vs `/dev/serial0`)

Quick checklist:

```bash
groups
ls /dev/ttyAMA0
ls /dev/serial0
```

If needed, try switching the port in the script to `/dev/serial0`.


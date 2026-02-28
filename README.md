# ugv01-x3-obstacle-avoidance
Simple floor-color + edge based obstacle avoidance for Waveshare UGV01-X3 (RPi 5 + ESP32 + Pi Camera)

# ugv01-x3-obstacle-avoidance

Simple floor-color + edge based obstacle avoidance for the Waveshare UGV01-X3 tracked robot.

This script lets the robot drive around autonomously on Raspberry Pi 5 + ESP32 (General Driver for Robots firmware) + Pi Camera.  
It avoids obstacles by looking at the color of the floor and detecting edges in the lower part of the camera view.

## How the robot works

- First it calibrates the floor color — drives slowly forward for about 1.4 seconds.
- Then it keeps checking the bottom third of the camera image: compares HSV colors to the calibrated floor and looks for edges with Canny.
- If everything looks clear — goes straight at medium speed.
- If it sees something different (obstacle, edge, dark spot) — stops and turns.
- If it gets stuck in a corner — switches to a special mode with small turns and occasional reverse to get out.

Commands are sent over UART (/dev/ttyAMA0, 115200 baud) — exactly the same JSON format you see in the official web control page (UGV01_BASE_WEB at http://192.168.4.1 in AP mode or local IP in STA).

## What hardware you need

- Waveshare UGV01-X3 tracked chassis (the one with good suspension)
- Raspberry Pi 5 (as the main brain)
- ESP32-WROOM-32 running General Driver for Robots firmware
- Raspberry Pi Camera (CSI port) — must be mounted on the front and looking straight forward (this is required!)
- 3×18650 batteries or some external power
- UART connection from Pi GPIO to ESP32 (usually /dev/ttyAMA0)

Note about the camera:  
It has to point forward. If you have a pan-tilt mount with servos — this script doesn't touch them. You can control servos separately through the web page or JSON commands if you want.

## One-time setup on Raspberry Pi

Install Raspberry Pi OS Bookworm 64-bit (Desktop or Lite — both work).

Then run: sudo raspi-config
Go to Interface Options:
- Serial Port → turn off login shell, turn on hardware port
- Camera → Enable
Finish and reboot.

Update everything: sudo apt update && sudo apt upgrade -y

Install system packages (recommended for camera and OpenCV on Raspberry Pi): 
sudo apt update
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-serial

## Installing libraries

Just run these two blocks:

```bash
# System packages — this is the reliable way for camera and OpenCV on Pi
sudo apt update
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-serial
```
## Quick Start (Installation & Run)
git clone https://github.com/tetotetodouga/ugv01-x3-obstacle-avoidance.git
cd ugv01-x3-obstacle-avoidance

sudo apt update
sudo apt install -y python3-opencv python3-picamera2 python3-numpy python3-serial

python3 avoid_obstacle.py
## Calibration & Tuning

### 1) Floor calibration (HSV)
On startup, the robot performs an automatic floor calibration:
- Captures ~35 HSV samples from a small center patch
- Slowly drives forward for ~1.4 seconds during sampling
- Uses the average HSV as the "floor color" reference

### 2) Region of Interest (ROI)
Obstacle detection is done in the lower part of the frame:

```python
y0 = int(h * 0.78)  # top boundary of ROI (default: 78% of frame height)
y1 = int(h * 0.95)  # bottom boundary of ROI (default: 95% of frame height)
```
If low obstacles are missed → lower y0 (e.g. 0.70–0.75)

If there are many false positives from the floor → raise y0 (e.g. 0.82–0.85)

### 3) Floor calibration patch (center sample area)

HSV patch used for floor calibration: patch = hsv[int(h * 0.90):int(h * 0.95), int(w * 0.46):int(w * 0.54)]
You can narrow/widen this patch if the floor is patterned, reflective, or non-uniform.

### 4) Detection thresholds

Sensitivity is controlled by these parameters:

Color difference threshold (center): DIFF_THR_CENTER = 25.0

Color difference threshold (sides): DIFF_THR_SIDE = 25.0

Canny edge count threshold (center): EDGE_THR_CENTER = 1800

Canny edge count threshold (sides): EDGE_THR_SIDE = 1400

If detection is too sensitive → increase thresholds slightly.
If the robot misses obstacles → decrease thresholds slightly.

## UART Check (Recommended)

After a reboot, it’s a good idea to confirm that the UART device exists and that your user has permission to use it.

### 1) Check that your user is in the `dialout` group
```bash
groups
```
If you don’t see dialout, add it (see Permission denied below).
### 2) Check that the serial devices exist
```bash
ls -l /dev/ttyAMA0
ls -l /dev/serial0
```
If UART is set up correctly, at least one of these devices should exist and be accessible by your user.
### Camera Troubleshooting
rpicam-hello does not start

## Possible causes

Camera is not connected

Ribbon cable is inserted the wrong way

Camera is disabled in Raspberry Pi settings

## Fix

Reseat the camera connector and cable

Make sure the ribbon cable contacts face the correct direction

Reboot the Raspberry Pi

## Image works, but the Python script can’t access the camera

Fix

Ensure picamera2 is installed:
```bash
sudo apt install python3-picamera2
```
Make sure the camera is not being used by another app at the same time (only one process can use it)
### Python Script Troubleshooting
ModuleNotFoundError

## Cause: a required library is missing.

## Fix: install the missing package (example):
```bash
sudo apt install python3-<package-name>
```
Permission denied when opening the serial port

## Cause: your user does not have access to UART.

## Fix:
```bash
sudo usermod -a -G dialout $USER
sudo reboot
```
### Robot moves incorrectly

## Possible causes

Wrong serial port selected

Wrong baud rate / serial settings

Obstacle detection thresholds/ROI are not tuned for your environment

## Fix

Try /dev/serial0 instead of /dev/ttyAMA0

Re-check wiring/connection between Raspberry Pi and the robot controller

Re-run and tune calibration/thresholds in the script
### UART Not Working (Robot Ignores Commands)
## Robot does not move after starting the program

## Possible causes

User permissions not set (not in dialout)

Serial Port is disabled in raspi-config

Wrong port selected

## Fix checklist

Confirm your user is in dialout:
```bash
groups
```
Confirm UART devices exist:
```bash
ls /dev/ttyAMA0
ls /dev/serial0
```
In raspi-config, make sure:

Serial console over UART is disabled

Serial Port hardware is enabled

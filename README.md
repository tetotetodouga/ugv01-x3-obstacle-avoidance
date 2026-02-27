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
Quick Start (Installation & Run)
git clone https://github.com/tetotetodouga/ugv01-x3-obstacle-avoidance.git
cd ugv01-x3-obstacle-avoidance

sudo apt update
sudo apt install -y python3-opencv python3-picamera2 python3-numpy python3-serial

python3 avoid_obstacle.py

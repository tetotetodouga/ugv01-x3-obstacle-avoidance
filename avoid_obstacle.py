import os 
import serial 
import time 
import cv2 
from picamera2 import Picamera2 
import numpy as np 
import random 
 
# ===================== REALVNC / DISPLAY FIX ===================== 
if not os.environ.get("DISPLAY"): 
    os.environ["DISPLAY"] = ":0" 
 
SHOW = True 
WIN_NAME = "Robot Camera (RealVNC) - press Q to stop" 
 
# ===================== SERIAL ===================== 
SERIAL_PORT = "/dev/ttyAMA0" 
# SERIAL_PORT = "/dev/serial0"
 
BAUDRATE = 115200 
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) 
 
def send(l, r): 
    ser.write(f'{{"T":1,"L":{l:.3f},"R":{r:.3f}}}\n'.encode()) 
    ser.flush() 
 
# init 
ser.write(b'{"T":143,"cmd":1}\n'); ser.flush() 
time.sleep(0.5) 
ser.write(b'{"T":131,"cmd":1}\n'); ser.flush() 
time.sleep(0.5) 
 
# ===================== CAMERA ===================== 
cam = Picamera2() 
cam.configure(cam.create_preview_configuration(main={"size": (640, 480)})) 
cam.start() 
 
# ===================== SPEED ===================== 
FWD_FAST = 0.28 
FWD_SLOW = 0.14 
TURN_SPEED = 0.22 
BACK = -0.16 
 
TURN_TIME = 0.65 
MICRO_TURN = TURN_TIME * (10.0 / 90.0) 
 
LOOP = 0.12 
STOP_AFTER_TURN = 0.25 
 
# ===================== ROI SETUP ===================== 
frame0 = cam.capture_array() 
h, w = frame0.shape[:2] 
 
y0 = int(h * 0.78) 
y1 = int(h * 0.95) 
 
LEFT   = (slice(y0, y1), slice(0, w // 3)) 
CENTER = (slice(y0, y1), slice(w // 5, w * 4 // 5)) 
RIGHT  = (slice(y0, y1), slice(w * 2 // 3, w)) 
 
# ===================== FLOOR CALIBRATION ===================== 
print("Calibrating floor... (slow move)") 
samples = [] 
send(FWD_SLOW, FWD_SLOW) 
t0 = time.time() 
 
while time.time() - t0 < 1.4: 
    f = cam.capture_array() 
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV) 
    patch = hsv[int(h * 0.90):int(h * 0.95), int(w * 0.46):int(w * 0.54)] 
    samples.append(np.mean(patch.reshape(-1, 3), axis=0)) 
    time.sleep(0.04) 
 
send(0.0, 0.0) 
time.sleep(0.15) 
 
floor_mean = np.median(samples, axis=0) 
print("Floor calibrated.") 
 
# ======= DIAGNOSTICS: guaranteed to drive for 1 second =======
print("DIAG: driving forward 1s to verify motors...") 
send(0.20, 0.20) 
time.sleep(1.0) 
send(0.0, 0.0) 
time.sleep(0.2) 
print("DIAG done.") 
 
def diff(box, hsv_img): 
    roi = hsv_img[box] 
    return float(np.linalg.norm(np.mean(roi.reshape(-1, 3), axis=0) - floor_mean)) 
 
def edge(box, gray_img): 
    g = cv2.GaussianBlur(gray_img[box], (5, 5), 0) 
    e = cv2.Canny(g, 60, 150) 
    return int(np.sum(e > 0)) 
 
# Thresholds (if it always thinks there’s a wall ahead, we’ll raise these thresholds).
DIFF_THR_CENTER = 25.0 
DIFF_THR_SIDE   = 25.0 
EDGE_THR_CENTER = 1800 
EDGE_THR_SIDE   = 1400 
 
def safe_turn(left, duration=TURN_TIME): 
    if left: 
        send(TURN_SPEED, -TURN_SPEED) 
    else: 
        send(-TURN_SPEED, TURN_SPEED) 
    time.sleep(duration) 
    send(0.0, 0.0) 
    time.sleep(STOP_AFTER_TURN) 
 
def micro_turn(left): 
    safe_turn(left, duration=MICRO_TURN) 
 
corner_mode = False 
corner_dir = True 
corner_steps = 0 
 
print(f"START on {SERIAL_PORT}. Press Q in window to stop.") 
 
try: 
    while True: 
        frame = cam.capture_array() 
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
 
        dL = diff(LEFT, hsv) 
        dC = diff(CENTER, hsv) 
        dR = diff(RIGHT, hsv) 
 
        eL = edge(LEFT, gray) 
        eC = edge(CENTER, gray) 
        eR = edge(RIGHT, gray) 
 
        blkL = (dL > DIFF_THR_SIDE)   or (eL > EDGE_THR_SIDE) 
        blkC = (dC > DIFF_THR_CENTER) or (eC > EDGE_THR_CENTER) 
        blkR = (dR > DIFF_THR_SIDE)   or (eR > EDGE_THR_SIDE) 
 
        print(f"blk L={int(blkL)} C={int(blkC)} R={int(blkR)} | dC={dC:.1f} eC={eC}") 
 
        if SHOW: 
            vis = frame.copy() 
            cv2.rectangle(vis, (0, y0), (w // 3, y1), (0, 255, 0), 2) 
            cv2.rectangle(vis, (w // 5, y0), (w * 4 // 5, y1), (0, 255, 0), 2) 
            cv2.rectangle(vis, (w * 2 // 3, y0), (w, y1), (0, 255, 0), 2) 
            cv2.putText(vis, f"blk L={int(blkL)} C={int(blkC)} R={int(blkR)}", 
                        (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2) 
            cv2.imshow(WIN_NAME, vis) 
            key = cv2.waitKey(1) & 0xFF 
            if key == ord("q"): 
                raise KeyboardInterrupt 
 
        # CORNER MODE 
        if corner_mode: 
            if not blkC: 
                corner_mode = False 
                corner_steps = 0 
                continue 
 
            micro_turn(corner_dir) 
            corner_steps += 1 
 
            if corner_steps > 18: 
                send(BACK, BACK); time.sleep(0.20) 
                send(0.0, 0.0); time.sleep(STOP_AFTER_TURN) 
                corner_dir = not corner_dir 
                corner_steps = 0 
            continue 
 
        # BLOCKED CENTER 
        if blkC: 
            send(0.0, 0.0) 
            time.sleep(STOP_AFTER_TURN) 
 
            if blkL and blkR: 
                corner_mode = True 
                corner_dir = random.choice([True, False]) 
                corner_steps = 0 
                continue 
 
            if not blkL and blkR: 
                safe_turn(True);  continue 
            if blkL and not blkR: 
                safe_turn(False); continue 
            if not blkL and not blkR: 
                safe_turn(random.choice([True, False])); continue 
 
            corner_mode = True 
            corner_dir = random.choice([True, False]) 
            corner_steps = 0 
            continue 
 
        # FORWARD 
        send(FWD_FAST, FWD_FAST) 
        time.sleep(LOOP) 
 
except KeyboardInterrupt: 
    print("STOP") 
 
finally: 
    try: send(0.0, 0.0) 
    except: pass 
    try: cam.stop() 
    except: pass 
    try: ser.close() 
    except: pass 
    try: cv2.destroyAllWindows() 
    except: pass 

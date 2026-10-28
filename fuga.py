import tkinter as tk
from tkinter import messagebox
import threading
import time
import pyperclip
import os
import subprocess
import shutil
import json
import urllib.request
import random
import math
import tempfile
import re
import sys
import base64
import glob
import struct 
import colorsys
import signal
import uuid
import string
import fcntl
import http.server
import socketserver

import hotmail_manager
import identity
import router_manager
import cleaner
import solver

SHARED_DIR = "/tmp"

class IPCRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == "/poll":
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            cmd = {}
            if hasattr(self.server, 'app_instance') and self.server.app_instance.pending_commands:
                cmd = self.server.app_instance.pending_commands.pop(0)
                
            self.wfile.write(json.dumps(cmd).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(raw_data)
            
            if hasattr(self.server, 'app_callback'):
                self.server.app_callback(payload)
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
        except Exception as e:
            print(f" [IPC Server] ❌ Error handling POST: {e}")
            self.send_response(500)
            self.end_headers()

try:
    INSTANCE_ID = int(sys.argv[1])
except:
    INSTANCE_ID = 1

MY_DISPLAY = f":{100 + (INSTANCE_ID - 1)}"
MY_DATA_DIR = os.path.expanduser(f"~/.config/BraveSoftware/Brave-Browser-{INSTANCE_ID}")


IPC_PORT = 8000 + INSTANCE_ID

hotmail_manager.INSTANCE_ID = INSTANCE_ID
router_manager.SESSION_FILE = f"session_cache_{INSTANCE_ID}.json"
router_manager.HISTORY_FILE = f"last_mru_{INSTANCE_ID}.txt"

router_manager.proxy_engine = None



def action_handler(env_vm, coords=None, action_type="click", target_out_of_viewport=False, abort_check=None, speed="normal"):
    
    speed_div = 3.0 if speed == "fast" else 1.0

    def is_aborted():
        if abort_check and abort_check():
            print("[!] 🧟 Zombie Thread Assassinated (Silent Exit).")
            sys.exit()
        return False
        
    try:
        if target_out_of_viewport:
            if is_aborted(): return
            scroll_ticks = random.randint(3, 9)
            ticks_done = 0
            
            while ticks_done < scroll_ticks:
                if is_aborted(): return
                flick_burst = random.randint(2, 4)
                flick_burst = min(flick_burst, scroll_ticks - ticks_done)
                
                for i in range(flick_burst):
                    if is_aborted(): return
                    subprocess.run(["xdotool", "click", "5"], env=env_vm) 
                    
                    if i == 0 or i == flick_burst - 1:
                        time.sleep(random.uniform(0.01, 0.02) / speed_div) 
                    else:
                        time.sleep(random.uniform(0.002, 0.007) / speed_div) 
                    ticks_done += 1
                
                if ticks_done < scroll_ticks:
                    time.sleep(random.uniform(0.04, 0.09) / speed_div)
            
            time.sleep(random.uniform(0.02, 0.05) / speed_div)

        if coords:
            if is_aborted(): return
            
            if 'x' in coords and 'y' in coords and 'tl' not in coords:
                target_x = int(coords['x']) + random.randint(-2, 2)
                target_y = int(coords['y']) + random.randint(-2, 2)
                
                w, h = 40, 40 
                
            else:
                w = int(coords['tr']['x'] - coords['tl']['x'])
                h = int(coords['bl']['y'] - coords['tl']['y'])
                
                center_x = int(coords['tl']['x'] + w / 2)
                center_y = int(coords['tl']['y'] + h / 2)
                
                safe_w = int(max(1, w * 0.15)) 
                safe_h = int(max(1, h * 0.15)) 
                
                target_x = random.randint(center_x - safe_w, center_x + safe_w)
                target_y = random.randint(center_y - safe_h, center_y + safe_h)

            res = subprocess.check_output(["xdotool", "getmouselocation", "--shell"], env=env_vm).decode()
            start_x = int(re.search(r'X=(\d+)', res).group(1))
            start_y = int(re.search(r'Y=(\d+)', res).group(1))
            
            distance = math.hypot(target_x - start_x, target_y - start_y)
            
            if distance < 15:
                subprocess.run(["xdotool", "mousemove", "--", str(target_x), str(target_y)], env=env_vm)
                time.sleep(random.uniform(0.02, 0.05) / speed_div)
            else:
                if action_type == "drag_release":
                    steps = random.randint(12, 27)
                    sleep_min, sleep_max = 0.019, 0.045
                else:
                    steps = random.randint(8, 18)
                    sleep_min, sleep_max = 0.013, 0.03 

                curve_pull = random.uniform(-0.5, 0.5) 
                path_style = random.choice(["c_curve", "s_curve", "late_hook"]) 
                
                for i in range(1, steps + 1):
                    if is_aborted(): return
                    t = i / steps
                    t_eased = 1 - (1 - t) ** 3
                    
                    curr_x = start_x + (target_x - start_x) * t_eased
                    curr_y = start_y + (target_y - start_y) * t_eased
                    
                    if path_style == "c_curve":
                        arc = math.sin(t * math.pi)
                    elif path_style == "s_curve":
                        arc = math.sin(t * math.pi * 2) * 0.5
                    else:
                        arc = math.sin((t ** 2) * math.pi)
                        
                    arc_factor = arc * distance * curve_pull
                    curr_x += arc_factor * 0.2
                    curr_y += arc_factor * 0.2
                    
                    tremor = (1.0 - t) * random.uniform(-2, 2)
                    
                    inter_x = int(curr_x + tremor)
                    inter_y = int(curr_y + tremor)
                    
                    subprocess.run(["xdotool", "mousemove", "--", str(inter_x), str(inter_y)], env=env_vm)
                    time.sleep(random.uniform(sleep_min, sleep_max) / speed_div)
                    
                if random.random() > 0.4: 
                    if is_aborted(): return
                    
                    safe_over_x = min(4, int(max(1, w * 0.05)))
                    safe_over_y = min(4, int(max(1, h * 0.05)))
                    
                    overshoot_x = target_x + random.randint(-safe_over_x, safe_over_x)
                    overshoot_y = target_y + random.randint(-safe_over_y, safe_over_y)
                    
                    subprocess.run(["xdotool", "mousemove", "--", str(overshoot_x), str(overshoot_y)], env=env_vm)
                    time.sleep(random.uniform(0.04, 0.08) / speed_div)
                    
                if is_aborted(): return
                subprocess.run(["xdotool", "mousemove", "--", str(target_x), str(target_y)], env=env_vm)
                time.sleep(random.uniform(0.04, 0.06) / speed_div)

        if is_aborted(): return
        if action_type == "move":
            return
            
        elif action_type == "click":
            subprocess.run(["xdotool", "mousedown", "1"], env=env_vm)
            time.sleep(random.uniform(0.07, 0.13) / speed_div)
            subprocess.run(["xdotool", "mouseup", "1"], env=env_vm)
            
        elif action_type == "drag_start":
            subprocess.run(["xdotool", "mousedown", "1"], env=env_vm)
            time.sleep(random.uniform(0.1, 0.2) / speed_div)
            
        elif action_type == "drag_release":
            time.sleep(random.uniform(0.1, 0.3) / speed_div)
            subprocess.run(["xdotool", "mouseup", "1"], env=env_vm)
            
        elif action_type == "scroll":
            scroll_ticks = random.randint(2, 6)
            ticks_done = 0
            
            while ticks_done < scroll_ticks:
                if is_aborted(): return
                flick_burst = random.randint(2, 4)
                flick_burst = min(flick_burst, scroll_ticks - ticks_done)
                
                for i in range(flick_burst):
                    if is_aborted(): return
                    subprocess.run(["xdotool", "click", "5"], env=env_vm) 
                    
                    if i == 0 or i == flick_burst - 1:
                        time.sleep(random.uniform(0.01, 0.02) / speed_div) 
                    else:
                        time.sleep(random.uniform(0.002, 0.007) / speed_div) 
                    ticks_done += 1
                
                if ticks_done < scroll_ticks:
                    time.sleep(random.uniform(0.04, 0.09) / speed_div)
                    
    except SystemExit:
        raise
    except Exception as e:
        print(f"[X] xdotool Action Handler Error: {e}")

def generate_identicon_bmp():
    width, height = 64, 64
    pixel_data = bytearray()
    
    row_size = width * 3
    padding = (4 - (row_size % 4)) % 4
    
    style = random.choice(["aura", "retro", "geo", "glitch", "deep"])
    print(f" [PFP] Generated Style: {style.upper()}")

    h1 = random.random()
    r1, g1, b1 = colorsys.hsv_to_rgb(h1, 0.8, 0.9)
    base_color = (int(b1*255), int(g1*255), int(r1*255))

    h2 = (h1 + random.uniform(0.1, 0.5)) % 1.0
    r2, g2, b2 = colorsys.hsv_to_rgb(h2, 0.8, 0.9)
    sec_color = (int(b2*255), int(g2*255), int(r2*255))

    shapes = []
    if style == "geo":
        for _ in range(random.randint(3, 6)):
            shapes.append({
                "type": random.choice(["circle", "rect"]),
                "x": random.randint(0, width),
                "y": random.randint(0, height),
                "size": random.randint(10, 30),
                "color": sec_color if random.random() > 0.5 else (255, 255, 255)
            })

    for y in range(height):
        row_bytes = bytearray()
        py = height - 1 - y
        
        for x in range(width):
            
            b, g, r = base_color
            
            if style == "aura":
                ratio = py / height
                b = int(base_color[0] * (1-ratio) + sec_color[0] * ratio)
                g = int(base_color[1] * (1-ratio) + sec_color[1] * ratio)
                r = int(base_color[2] * (1-ratio) + sec_color[2] * ratio)

            elif style == "retro":
                band_size = 12
                if (py // band_size) % 2 == 0:
                    b, g, r = sec_color

            elif style == "geo":
                for s in shapes:
                    if s["type"] == "rect":
                        if abs(x - s["x"]) < s["size"] and abs(py - s["y"]) < s["size"]:
                            b, g, r = s["color"]
                    elif s["type"] == "circle":
                        dist = ((x - s["x"])**2 + (py - s["y"])**2)**0.5
                        if dist < s["size"]:
                            b, g, r = s["color"]

            elif style == "glitch":
                if random.random() > 0.85:
                    tn = random.random()
                    rn, gn, bn = colorsys.hsv_to_rgb(tn, 1.0, 1.0)
                    b, g, r = int(bn*255), int(gn*255), int(rn*255)

            elif style == "deep":
                cx, cy = width//2, height//2
                dist = ((x - cx)**2 + (py - cy)**2)**0.5
                max_dist = (cx**2 + cy**2)**0.5
                factor = 1.0 - (dist / max_dist)
                
                b = int(base_color[0] * factor)
                g = int(base_color[1] * factor)
                r = int(base_color[2] * factor)

            row_bytes += bytes([b, g, r])
        
        row_bytes += bytes(padding)
        pixel_data += row_bytes

    file_size = 54 + len(pixel_data)
    header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
    dib = struct.pack('<IIIHHIIIIII', 40, width, height, 1, 24, 0, len(pixel_data), 2835, 2835, 0, 0)
    
    full_bmp = header + dib + pixel_data
    b64_str = base64.b64encode(full_bmp).decode('utf-8')
    return f'"data:image/bmp;base64,{b64_str}"'


class ExtensionGenerator:
    
    GPU_DB = [
        ("ATI Technologies Inc.", "AMD Radeon RX 6950 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6900 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6800 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6800"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6750 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6700 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6650 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6600 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6600"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6500 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6400"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2080 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2080 Super"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2080"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070 Super"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2060 Super"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2060"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Super"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650 Super"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4090"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4080"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4080 Super"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4070 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4070"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4060 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4060"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3090 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3090"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3080 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3080"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3050"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1080 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1080"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1070 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1070"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060 6GB"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060 3GB"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050"),
        
        ("ATI Technologies Inc.", "AMD Radeon RX 7900 XTX"),
        ("ATI Technologies Inc.", "AMD Radeon RX 7900 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 7800 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 7700 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 7600"),
        
        ("ATI Technologies Inc.", "AMD Radeon RX 5700 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 5700"),
        ("ATI Technologies Inc.", "AMD Radeon RX 5600 XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 5500 XT"),
        
        ("ATI Technologies Inc.", "AMD Radeon RX 590"),
        ("ATI Technologies Inc.", "AMD Radeon RX 580"),
        ("ATI Technologies Inc.", "AMD Radeon RX 570"),
        ("ATI Technologies Inc.", "AMD Radeon RX 560"),
        ("ATI Technologies Inc.", "AMD Radeon RX 550"),
        ("ATI Technologies Inc.", "AMD Radeon RX 480"),
        ("ATI Technologies Inc.", "AMD Radeon RX 470"),
        ("ATI Technologies Inc.", "AMD Radeon RX 460"),
        
        ("ATI Technologies Inc.", "AMD Radeon VII"),
        ("ATI Technologies Inc.", "AMD Radeon RX Vega 64"),
        ("ATI Technologies Inc.", "AMD Radeon RX Vega 56"),

        
        ("NVIDIA Corporation", "NVIDIA Quadro T1000"),
        ("NVIDIA Corporation", "NVIDIA Quadro T600"),
        ("NVIDIA Corporation", "NVIDIA Quadro T400"),
        
        ("NVIDIA Corporation", "NVIDIA Quadro P5000"),
        ("NVIDIA Corporation", "NVIDIA Quadro P4000"),
        ("NVIDIA Corporation", "NVIDIA Quadro P2200"),
        ("NVIDIA Corporation", "NVIDIA Quadro P2000"),
        ("NVIDIA Corporation", "NVIDIA Quadro P1000"),
        ("NVIDIA Corporation", "NVIDIA Quadro P620"),
        ("NVIDIA Corporation", "NVIDIA Quadro P600"),
        ("NVIDIA Corporation", "NVIDIA Quadro P400"),

        ("NVIDIA Corporation", "NVIDIA Quadro M4000"),
        ("NVIDIA Corporation", "NVIDIA Quadro M2000"),
        ("NVIDIA Corporation", "NVIDIA Quadro M1200"),
        ("NVIDIA Corporation", "NVIDIA Quadro M620"),

        ("NVIDIA Corporation", "NVIDIA Quadro K4200"),
        ("NVIDIA Corporation", "NVIDIA Quadro K2200"),
        ("NVIDIA Corporation", "NVIDIA Quadro K1200"),
        ("NVIDIA Corporation", "NVIDIA Quadro K620"),
        ("NVIDIA Corporation", "NVIDIA Quadro K2000"),
        ("NVIDIA Corporation", "NVIDIA Quadro K600"),

        ("NVIDIA Corporation", "NVIDIA RTX A5000"),
        ("NVIDIA Corporation", "NVIDIA RTX A4500"),
        ("NVIDIA Corporation", "NVIDIA RTX A4000"),
        ("NVIDIA Corporation", "NVIDIA RTX A2000"),

        ("NVIDIA Corporation", "NVIDIA GeForce GTX 980 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 980"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 970"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 960"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 950"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 750 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 750"),
        
        ("NVIDIA Corporation", "NVIDIA Quadro M5000M"),
        ("NVIDIA Corporation", "NVIDIA Quadro M4000M"),
        ("NVIDIA Corporation", "NVIDIA Quadro M3000M"),
        ("NVIDIA Corporation", "NVIDIA Quadro M2200"),
        ("NVIDIA Corporation", "NVIDIA Quadro M2000M"),
        ("NVIDIA Corporation", "NVIDIA Quadro M1000M"),
        ("NVIDIA Corporation", "NVIDIA Quadro M500M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K5100M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K4100M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K3100M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K2200M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K2100M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K1100M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K2000M"),
        ("NVIDIA Corporation", "NVIDIA Quadro K1000M"),
        
        ("ATI Technologies Inc.", "AMD Radeon R9 M390X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 M295X"),
        ("ATI Technologies Inc.", "AMD Radeon R7 M445"),
        ("ATI Technologies Inc.", "AMD Radeon R7 M440"),
        ("ATI Technologies Inc.", "AMD Radeon R7 M360"),
        ("ATI Technologies Inc.", "AMD Radeon R7 M340"),
        ("ATI Technologies Inc.", "AMD Radeon R7 M265"),
        ("ATI Technologies Inc.", "AMD Radeon R7 M260"),
        ("ATI Technologies Inc.", "AMD Radeon R5 M430"),
        ("ATI Technologies Inc.", "AMD Radeon R5 M335"),
        ("ATI Technologies Inc.", "AMD Radeon R5 M330"),
        ("ATI Technologies Inc.", "AMD Radeon R5 M230"),
        ("ATI Technologies Inc.", "AMD Radeon HD 8970M"),
        ("ATI Technologies Inc.", "AMD Radeon HD 8870M"),
        ("ATI Technologies Inc.", "AMD Radeon HD 8790M"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7970M"),
        
        ("ATI Technologies Inc.", "AMD Radeon R9 Fury X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 Fury"),
        ("ATI Technologies Inc.", "AMD Radeon R9 Nano"),
        ("ATI Technologies Inc.", "AMD Radeon R9 390X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 390"),
        ("ATI Technologies Inc.", "AMD Radeon R9 380X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 380"),
        ("ATI Technologies Inc.", "AMD Radeon R9 290X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 290"),
        ("ATI Technologies Inc.", "AMD Radeon R9 280X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 280"),
        ("ATI Technologies Inc.", "AMD Radeon R9 270X"),
        ("ATI Technologies Inc.", "AMD Radeon R9 270"),
        ("ATI Technologies Inc.", "AMD Radeon R7 370"),
        ("ATI Technologies Inc.", "AMD Radeon R7 360"),
        ("ATI Technologies Inc.", "AMD Radeon R7 265"),
        ("ATI Technologies Inc.", "AMD Radeon R7 260X"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7990"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7970 GHz Edition"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7970"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7950"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7870"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7850"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7790"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7770"),
        ("ATI Technologies Inc.", "AMD Radeon HD 7750"),

        ("NVIDIA Corporation", "NVIDIA GeForce MX570"),
        ("NVIDIA Corporation", "NVIDIA GeForce MX550"),
        ("NVIDIA Corporation", "NVIDIA GeForce MX450"),
        ("NVIDIA Corporation", "NVIDIA GeForce MX350"),
        ("NVIDIA Corporation", "NVIDIA GeForce MX330"),
        ("NVIDIA Corporation", "NVIDIA GeForce MX250"),
        ("NVIDIA Corporation", "NVIDIA GeForce MX150"),
        ("NVIDIA Corporation", "NVIDIA GeForce 940MX"),

        ("ATI Technologies Inc.", "AMD Radeon Pro W5700"),
        ("ATI Technologies Inc.", "AMD Radeon Pro W5500"),
        ("ATI Technologies Inc.", "AMD Radeon Pro WX 7100"),
        ("ATI Technologies Inc.", "AMD Radeon Pro WX 5100"),
        ("ATI Technologies Inc.", "AMD Radeon Pro WX 4100"),
        ("ATI Technologies Inc.", "AMD Radeon Pro WX 3100"),
        ("ATI Technologies Inc.", "AMD Radeon Pro WX 2100"),

        ("ATI Technologies Inc.", "AMD Radeon(TM) 780M"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) 680M"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) Vega 11 Graphics"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) Vega 8 Graphics"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) Vega 3 Graphics"),
        
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics"),
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics 655"),
        ("Intel Inc.", "Intel(R) Iris(R) Plus Graphics 640"),
        ("Intel Inc.", "Intel(R) HD Graphics 615"),
        ("Intel Inc.", "Intel(R) HD Graphics 6000"),
        ("Intel Inc.", "Intel(R) HD Graphics 5500"),
        ("Intel Inc.", "Intel(R) HD Graphics 5000"),
        ("Intel Inc.", "Intel(R) HD Graphics 4600"),
        ("Intel Inc.", "Intel(R) HD Graphics 4400"),
        ("Intel Inc.", "Intel(R) HD Graphics 4000"),
        
        

        ("ATI Technologies Inc.", "AMD Radeon(TM) 530"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) 540"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) 620"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) 610M"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) R7 Graphics"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) R5 Graphics"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) R4 Graphics"),
        ("ATI Technologies Inc.", "AMD Radeon(TM) R3 Graphics"),

        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050 Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 960M"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 950M"),
        ("NVIDIA Corporation", "NVIDIA GeForce GT 1030"),
        ("NVIDIA Corporation", "NVIDIA GeForce GT 730"),
        ("NVIDIA Corporation", "NVIDIA GeForce GT 710"),
        
        ("ATI Technologies Inc.", "AMD Radeon R7 450"),
        ("ATI Technologies Inc.", "AMD Radeon R7 430"),
        ("ATI Technologies Inc.", "AMD Radeon R7 250"),
        ("ATI Technologies Inc.", "AMD Radeon R7 240"),
        ("ATI Technologies Inc.", "AMD Radeon R5 430"),
        ("ATI Technologies Inc.", "AMD Radeon R5 340X"),
        ("ATI Technologies Inc.", "AMD Radeon R5 240"),
        ("NVIDIA Corporation", "NVIDIA GeForce GT 740"), 
        ("NVIDIA Corporation", "NVIDIA GeForce GT 640"),
        ("NVIDIA Corporation", "NVIDIA GeForce GT 630"),

        ("Intel Inc.", "Intel(R) UHD Graphics 605"),
        ("Intel Inc.", "Intel(R) UHD Graphics 600"),
        ("Intel Inc.", "Intel(R) HD Graphics 505"),
        ("Intel Inc.", "Intel(R) HD Graphics 500"),
        ("Intel Inc.", "Intel(R) HD Graphics 405"),
        ("Intel Inc.", "Intel(R) HD Graphics 400"),

        ("Intel Inc.", "Intel(R) UHD Graphics 730"),
        ("Intel Inc.", "Intel(R) UHD Graphics 710"),
        ("Intel Inc.", "Intel(R) UHD Graphics 610"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 860M"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 850M"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 765M"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 760M"),
        ("ATI Technologies Inc.", "AMD Radeon R9 M375"),
        ("ATI Technologies Inc.", "AMD Radeon R9 M290X"),
        
        ("Intel Inc.", "Intel(R) Iris(R) Graphics 540"),
        ("Intel Inc.", "Intel(R) Iris(R) Graphics 520"), 
        ("Intel Inc.", "Intel(R) HD Graphics 515"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3080 Ti Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3080 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070 Ti Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3070 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3050 Ti Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3050 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3050 OEM"),

        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2080 Super with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2080 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070 Super with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070 Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2060 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2060 Mobile"),

        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Ti with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1660 Ti Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650 Ti with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1650 Mobile"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce GTX TITAN X"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX TITAN Black"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX TITAN"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 780 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 780"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 770"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 760"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 690"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 680"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 670"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 660 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 660"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 650 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 650"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 580"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 570"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 560 Ti"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 560"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 550 Ti"),

        ("ATI Technologies Inc.", "AMD Radeon RX 6850M XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6800M"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6800S"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6700M"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6700S"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6650M XT"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6650M"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6600M"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6600S"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6500M"),
        ("ATI Technologies Inc.", "AMD Radeon RX 6300M"),

        ("NVIDIA Corporation", "NVIDIA RTX 5000 Ada Generation Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX 4000 Ada Generation Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX 3500 Ada Generation Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX 3000 Ada Generation Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX 2000 Ada Generation Laptop GPU"),
        
        ("NVIDIA Corporation", "NVIDIA RTX A5500 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A5000 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A4500 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A4000 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A3000 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A2000 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A1000 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA RTX A500 Laptop GPU"),

        ("NVIDIA Corporation", "NVIDIA T1200 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA T600 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA T550 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA T500 Laptop GPU"),
        ("NVIDIA Corporation", "NVIDIA Quadro T2000 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA Quadro T1000 with Max-Q Design"),
        
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1080 Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1080 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1070 Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1070 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060 Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060 with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050 Ti Mobile"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050 Ti with Max-Q Design"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050 with Max-Q Design"),
    ]
    
    UA_DB = [
        ("138", "138.0.7000.115"),
        ("139", "139.0.7100.120"),
        ("140", "140.0.7250.90"),
        ("141", "141.0.7400.100"),
        ("142", "142.0.7550.110"),
        ("143", "143.0.7700.80"),
        ("144", "144.0.7800.50"),
        ("145", "145.0.7950.30")
    ]
    
    
    def __init__(self):
        self.base_dir = None
        self.current_gpu_index = 0

    def create_extension(self, avatar_payload=None, is_unclaimed=False, trial_token=None, use_solver=True):
        for folder in glob.glob(f"fuga_extension_{INSTANCE_ID}_*"):
            try:
                shutil.rmtree(os.path.abspath(folder))
                print(f" [Cleaner] 🗑️ Deleted orphaned extension: {folder}")
            except Exception as e:
                print(f" [Cleaner] ⚠️ Could not delete {folder}: {e}")

        rand_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.base_dir = os.path.abspath(f"fuga_extension_{INSTANCE_ID}_{rand_hash}")

        try:
            os.makedirs(self.base_dir)
        except Exception as e: 
            return None, "Error"

        
        vendor, renderer = random.choice(self.GPU_DB)
        
        ua_major, ua_full = random.choice(self.UA_DB)
        
        poison_r = random.random()
        poison_g = random.random()
        poison_b = random.random()
        poison_a = random.uniform(0.001, 0.01)
        poison_x = random.randint(0, 5)
        poison_y = random.randint(0, 5)
        
        audio_noise_val = random.uniform(0.000001, 0.0001)
        audio_step = random.randint(50, 150)
        
        stealth_names = [
            "Chrome Media Router",
            "Google Network Speech Synthesizer",
            "Chrome PDF Viewer",
            "CryptoTokenExtension",
            "Brave Shields UI",
            "Application Launcher for Drive",
            "Google Hangouts",
            "Web Store",
            "Cloud Print",
            "WebRTC Control Core"
        ]
        random_ext_name = random.choice(stealth_names)
        
        random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 99)}"


        manifest = {

            "manifest_version": 3,

            "name": random_ext_name,
            "version": random_version,


            "permissions": ["webRequest", "declarativeNetRequest", "declarativeNetRequestWithHostAccess", "scripting", "storage"],

            "host_permissions": ["<all_urls>"],

            "background": { "service_worker": "background.js" },

            "declarative_net_request": { 

                "rule_resources": [{ "id": "ruleset_1", "enabled": True, "path": "rules.json" }] 

            },

            "content_scripts": [
                { 
                    "matches": ["<all_urls>"], 
                    "all_frames": True, 
                    "match_about_blank": True, 
                    "match_origin_as_fallback": True, 
                    "js": ["inject.js"], 
                    "run_at": "document_start", 
                    "world": "MAIN" 
                },
                { 
                    "matches": ["<all_urls>"], 
                    "all_frames": True, 
                    "match_about_blank": True, 
                    "match_origin_as_fallback": True, 
                    "js": ["observer.js"], 
                    "run_at": "document_idle", 
                    "world": "ISOLATED" 
                }
            ]

        }




        rules = [{

            "id": 1,

            "priority": 1,

            "action": { 

                "type": "modifyHeaders", 

                "responseHeaders": [

                    { "header": "content-security-policy", "operation": "remove" },

                    { "header": "x-content-security-policy", "operation": "remove" }

                ],

                "requestHeaders": [

                    { "header": "User-Agent", "operation": "set", "value": f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{ua_major}.0.0.0 Safari/537.36" },

                    { "header": "Sec-CH-UA", "operation": "set", "value": f'"Not(A:Brand";v="99", "Google Chrome";v="{ua_major}", "Chromium";v="{ua_major}"' },

                    { "header": "Sec-CH-UA-Full-Version-List", "operation": "set", "value": f'"Not(A:Brand";v="99.0.0.0", "Google Chrome";v="{ua_full}", "Chromium";v="{ua_full}"' },

                    { "header": "Sec-CH-UA-Platform", "operation": "set", "value": '"Linux"' },

                    { "header": "Sec-CH-UA-Mobile", "operation": "set", "value": "?0" }

                ]

            },

            "condition": { "urlFilter": "|http*", "resourceTypes": ["main_frame", "sub_frame", "xmlhttprequest", "script", "other"] }

        }]


        creepjs_targets = [
            "HTMLCanvasElement.prototype.toBlob",
            "CanvasRenderingContext2D.prototype.getImageData",
            "Element.prototype.append",
            "Element.prototype.prepend",
            "Element.prototype.replaceWith",
            "Node.prototype.insertBefore",
            "AnalyserNode.prototype.getByteFrequencyData",
            "AnalyserNode.prototype.getFloatFrequencyData",
            "Navigator.prototype.hardwareConcurrency",
            "Screen.prototype.availHeight",
            "Screen.prototype.colorDepth",
            "Screen.prototype.pixelDepth"
        ]
        sel_decoys = random.sample(creepjs_targets, random.randint(2, 6))
        decoy_js = ""
        for api in sel_decoys:
            obj, prop = api.rsplit('.', 1)
            decoy_js += f"""
            try {{
                const targetObj = win.{obj};
                if (targetObj) {{
                    const desc = Object.getOwnPropertyDescriptor(targetObj, '{prop}');
                    if (desc && desc.get) {{
                        desc.get = new Proxy(desc.get, {{ apply(t, ta, a) {{ return Reflect.apply(t, ta, a); }} }});
                        Object.defineProperty(targetObj, '{prop}', desc);
                    }} else if (targetObj['{prop}']) {{
                        targetObj['{prop}'] = new Proxy(targetObj['{prop}'], {{ apply(t, ta, a) {{ return Reflect.apply(t, ta, a); }} }});
                    }}
                }}
            }} catch(e) {{}}
            """
            
        sec_pool = [
            'FileSystemWritableFileStream', 'Serial', 'ReportingObserver',
            'OfflineAudioContext', 'RTCRtpTransceiver', 'MediaDevices', 'Credential'
        ]
        sel_sec = random.sample(sec_pool, random.randint(1, 4))
        sec_js = ""
        for prop in sel_sec:
            sec_js += f"try {{ delete win.{prop}; delete win.Window.prototype.{prop}; }} catch(e) {{}}\n"

        def ast_noise(): return f"const v_{''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))} = {random.randint(10000, 99999)};"
        
        token_injection_js = ""
        if trial_token:
            token_injection_js = f"""
            // [TRIAL MODE] 100% STEALTH PRE-LOAD INJECTION
            try {{
                const t = '{trial_token}';
                window.localStorage.setItem('token', '"' + t + '"');
                
                // Hook the getter temporarily to intercept early app reads
                const origGetItem = Storage.prototype.getItem;
                Storage.prototype.getItem = function(key) {{
                    if (key === 'token') return '"' + t + '"';
                    return origGetItem.apply(this, arguments);
                }};
            }} catch(e) {{}}
            """

        js_code = f"""

        (function() {{

            const CONF = {{ 

                vendor: "{vendor}", renderer: "{renderer}", 

                r: {poison_r}, g: {poison_g}, b: {poison_b}, a: {poison_a},

                x: {poison_x}, y: {poison_y},

                a_noise: {audio_noise_val}, a_step: {audio_step},

                ua_major: "{ua_major}",

                ua_full: "{ua_full}"
            }};
            
            
            const SPOOF_CORE = `

                // Wrap everything in an IIFE to guarantee ZERO global namespace pollution

                (() => {{

                    const CONF = ${{JSON.stringify(CONF)}};

                    const spoofedWindows = new WeakSet();

                    const toStringMap = new WeakMap();

                    const hookedToStrings = new WeakSet();

                    const hookedContexts = new WeakSet();

                    

                    const registerNative = (fn, name) => {{

                        toStringMap.set(fn, "function " + name + "() {{ [native code] }}");

                    }};


                    // Shared variables for the entire scope

                    let poisonDraw;

                    const fakeUA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/" + CONF.ua_major + ".0.0.0 Safari/537.36";

                    const fakeAppVersion = "5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/" + CONF.ua_major + ".0.0.0 Safari/537.36";

                    const fakePlatform = "Linux x86_64";


                    function applySpoof(win) {{

                        // Lock to prevent infinite recursion and duplicate spoofing using closure WeakSet

                        if (!win || spoofedWindows.has(win)) return;

                        spoofedWindows.add(win);
                        
                        {token_injection_js}

                        // --- INJECT DECOY LIES TO SCRAMBLE CREEPJS PATTERN HASH ---
                        {decoy_js}
                        
                        // --- INJECT SECURITY HASH SCRAMBLER ---
                        {sec_js}

                        // --- [BRAVE MANIPULATION REMOVED FOR STABILITY] ---


                        // --- THE NUCLEAR CORE: WEAKMAP TOSTRING REGISTRY ---
                        try {{
                            if (win.Function && !hookedToStrings.has(win.Function.prototype.toString)) {{
                                const origToString = win.Function.prototype.toString;
                                
                                const toStringProxy = new Proxy(origToString, {{
                                    apply: function(target, thisArg, args) {{
                                        // 1. Intercept our spoofed functions
                                        if (typeof thisArg === 'function' && toStringMap.has(thisArg)) {{
                                            return toStringMap.get(thisArg);
                                        }}
                                        
                                        // 2. Protect the proxy itself with the exact dynamic native string
                                        if (thisArg === toStringProxy) {{
                                            return Reflect.apply(target, target, args);
                                        }}
                                        
                                        // 3. Forward to native engine and SCRUB THE STACK TRACE LEAK!
                                        try {{
                                            return Reflect.apply(target, thisArg, args);
                                        }} catch (err) {{
                                            if (err && typeof err.stack === 'string') {{
                                                const nl = String.fromCharCode(10);
                                                err.stack = err.stack.split(nl).filter(function(line) {{
                                                    return !line.includes('Reflect.apply') && 
                                                           !line.includes('Proxy.apply') && 
                                                           !line.includes('apply@');
                                                }}).join(nl);
                                            }}
                                            throw err;
                                        }}
                                    }}
                                }});
                                
                                win.Function.prototype.toString = toStringProxy;
                                hookedToStrings.add(toStringProxy);
                            }}
                        }} catch(e) {{}}


                        // --- [B] NAVIGATOR SPOOFING (Main Thread) ---

                        try {{

                            if (win.navigator) {{

                                const navProto = Object.getPrototypeOf(win.navigator);

                                

                                const hookGetter = (prop, fakeValue) => {{

                                    const desc = Object.getOwnPropertyDescriptor(navProto, prop);

                                    if (desc && desc.get) {{

                                        const origGet = desc.get;

                                        const newGet = function() {{

                                            origGet.call(this); 

                                            return fakeValue;

                                        }};

                                        registerNative(newGet, "get " + prop);

                                        desc.get = newGet;

                                        Object.defineProperty(navProto, prop, desc);

                                    }}

                                }};


                                hookGetter('userAgent', fakeUA);

                                hookGetter('appVersion', fakeAppVersion);

                                hookGetter('platform', fakePlatform);


                                // Spoof User Agent Data (Sec-CH-UA Client Hints)

                                if (win.navigator.userAgentData) {{

                                    const uadProto = Object.getPrototypeOf(win.navigator.userAgentData);

                                    const fakeUaData = {{

                                        architecture: "x86",

                                        bitness: "64",

                                        brands: [

                                            {{ brand: "Not(A:Brand", version: "99" }},

                                            {{ brand: "Google Chrome", version: CONF.ua_major }},

                                            {{ brand: "Chromium", version: CONF.ua_major }}

                                        ],

                                        fullVersionList: [

                                            {{ brand: "Not(A:Brand", version: "99.0.0.0" }},

                                            {{ brand: "Google Chrome", version: CONF.ua_full }},

                                            {{ brand: "Chromium", version: CONF.ua_full }}

                                        ],

                                        uaFullVersion: CONF.ua_full,

                                        mobile: false,

                                        model: "",

                                        platform: "Linux",

                                        platformVersion: ""

                                    }};


                                    ['brands', 'mobile', 'platform'].forEach(prop => {{

                                        const desc = Object.getOwnPropertyDescriptor(uadProto, prop);

                                        if (desc && desc.get) {{

                                            const origGet = desc.get;

                                            const newGet = function() {{

                                                origGet.call(this);

                                                return fakeUaData[prop];

                                            }};

                                            registerNative(newGet, "get " + prop);

                                            desc.get = newGet;

                                            Object.defineProperty(uadProto, prop, desc);

                                        }}

                                    }});


                                    const getHighDesc = Object.getOwnPropertyDescriptor(uadProto, 'getHighEntropyValues');

                                    if (getHighDesc && getHighDesc.value) {{

                                        const origHigh = getHighDesc.value;

                                        const newHigh = function getHighEntropyValues(hints) {{

                                            return origHigh.call(this, hints).then(orig => {{

                                                const result = {{ brands: fakeUaData.brands, mobile: fakeUaData.mobile }};

                                                const h = hints || [];

                                                h.forEach(hint => {{

                                                    if (fakeUaData[hint] !== undefined) result[hint] = fakeUaData[hint];

                                                    else if (orig[hint] !== undefined) result[hint] = orig[hint];

                                                }});

                                                return result;

                                            }});

                                        }};

                                        registerNative(newHigh, "getHighEntropyValues");

                                        getHighDesc.value = newHigh;

                                        Object.defineProperty(uadProto, 'getHighEntropyValues', getHighDesc);

                                    }}

                                }}

                            }}

                        }} catch(e) {{}}
                        
                        // --- [F] WEBRTC SDP SCRAMBLER ---
                        try {{
                            const rtcProto = win.RTCPeerConnection ? win.RTCPeerConnection.prototype : (win.webkitRTCPeerConnection ? win.webkitRTCPeerConnection.prototype : null);
                            if (rtcProto && rtcProto.createOffer) {{
                                const origCreateOffer = rtcProto.createOffer;
                                rtcProto.createOffer = function createOffer() {{
                                    {ast_noise()}
                                    const _this = this;
                                    const _args = arguments;
                                    return origCreateOffer.apply(_this, _args).then(function(offer) {{
                                        if (offer && offer.sdp) {{
                                            const randId = {random.randint(1000000, 9999999)};
                                            // 4x backslashes to survive Python -> Template Literal -> eval()
                                            const fakeExt = "a=extmap:255 urn:ietf:params:rtp-hdrext:fuga-" + randId + "\\\\x0D\\\\x0A";
                                            const modifiedSdp = offer.sdp.replace(/(m=[^\\\\x0D\\\\x0A]+\\\\x0D\\\\x0A)/, "$1" + fakeExt);
                                            
                                            return {{
                                                type: offer.type,
                                                sdp: modifiedSdp
                                            }};
                                        }}
                                        return offer;
                                    }});
                                }};
                                registerNative(rtcProto.createOffer, 'createOffer');
                            }}
                        }} catch(e) {{}}
                        
                        
                        // --- [G] GLOBAL IFRAME LEAK FIIX ----

                        try {{

                            const safeApply = function(cw) {{

                                if (!cw) return cw;

                                try {{

                                    if (cw.location && !spoofedWindows.has(cw)) {{

                                        applySpoof(cw);

                                    }}

                                }} catch(err) {{

                                    // Silent fail for Cross-Origin iframes

                                }}

                                return cw;

                            }};


                            if (win.document && win.document.createElement) {{

                                const origCreateElement = win.document.createElement;

                                win.document.createElement = function createElement(tagName, options) {{

                                    const element = origCreateElement.call(this, tagName, options);

                                    if (tagName && tagName.toLowerCase() === 'iframe') {{

                                        const checkIframe = setInterval(() => {{

                                            if (element.contentWindow) {{

                                                safeApply(element.contentWindow);

                                                clearInterval(checkIframe);

                                            }}

                                        }}, 10);

                                        setTimeout(() => clearInterval(checkIframe), 2000);

                                    }}

                                    return element;

                                }};

                                registerNative(win.document.createElement, "createElement");

                            }}


                            if (win.HTMLIFrameElement && win.HTMLIFrameElement.prototype) {{

                                const iframeContentWindow = Object.getOwnPropertyDescriptor(win.HTMLIFrameElement.prototype, 'contentWindow');

                                if (iframeContentWindow) {{

                                    const originalGet = iframeContentWindow.get;

                                    Object.defineProperty(win.HTMLIFrameElement.prototype, 'contentWindow', {{

                                        get: function() {{

                                            return safeApply(originalGet.call(this));

                                        }},

                                        set: iframeContentWindow.set || function() {{}}

                                    }});

                                }}

                            }}

                            

                            if (win.Node && win.Node.prototype) {{

                                const oldAppend = win.Node.prototype.appendChild;

                                win.Node.prototype.appendChild = function appendChild(child) {{

                                    const res = oldAppend.apply(this, arguments);

                                    if (child && child.nodeName === 'IFRAME') {{

                                        safeApply(child.contentWindow);

                                    }}

                                    return res;

                                }};

                                registerNative(win.Node.prototype.appendChild, "appendChild");

                            }}

                        }} catch(e) {{}}

                    }}

                    

                    applySpoof(typeof window !== 'undefined' ? window : self);

                }})();

            `;


            try {{ eval(SPOOF_CORE); }} catch(e) {{}}

            try {{ delete navigator.serviceWorker; Object.defineProperty(navigator, 'serviceWorker', {{get: () => undefined}}); }} catch(e) {{}}
            


        }})();

        """ 
        
        target_quest_id = random.choice(['1527015843882340402'])
        
        js_is_trial = str(bool(trial_token)).lower()
        js_is_unclaimed = str(is_unclaimed).lower()
        js_avatar = avatar_payload if avatar_payload == "null" else f"'{avatar_payload}'"
        js_is_solver_active = "true" if use_solver else "false"

        observer_js_code = f"""
        (() => {{
            // --- INTERNAL CONFIG (Injected from Python) ---
            const isSolverActive = {js_is_solver_active};
            const isTrialMode = {js_is_trial};
            const isUnclaimedMode = {js_is_unclaimed};
            const avatarData = {js_avatar};

            // --- INTERNAL STATE ---
            let captured_token = "";
            let captured_super_props = "";
            let pfp_attempted = false;
            let trial_quest_started = false;
            
            let loginSent = false;
            let dashboardSent = false;
            let verifiedSent = false;
            let tosSent = false;
            let createSent = false;
            let closeSent = false;
            let dobMonthSent = false;
            let dobDaySent = false;
            let dobYearSent = false;
            let currentDropdownId = "";
            let createScrollFlagSent = false;
            let hcaptchaSent = false;
            let hcaptchaCheckboxSent = false;
            let skipCycleSent = false;
            let unavailableEntrySent = false;



            // --- 0. HCAPTCHA BASE64 EXTRACTOR (ULTRA-STEALTH) ---
            // Local memory flag
            // 100% Stealth Memory tracking. Leaves zero trace on the hCaptcha DOM.
            const fugaObservedNodes = new WeakSet();
            let fugaSyncLock = false;
            const captureHcaptcha = async () => {{

                // Check Chrome Storage. If the 5-second lock is active, silently abort.
                const lockCheck = await chrome.storage.local.get('fugaGlobalCooldown');
                if (lockCheck.fugaGlobalCooldown) {{
                    return null; 
                }}

                // 1. Get the unique hCaptcha widget ID and Frame Type from this specific iframe's URL
                const hashParams = new URLSearchParams(window.location.hash.substring(1));
                const widgetId = hashParams.get('id') || 'fallback_id';
                const frameType = hashParams.get('frame') || 'challenge'; 

                // 2. Tell the Top Window: "I am ready. Find my exact iframe and measure me."
                await chrome.storage.local.set({{ fugaIdentifyMe: widgetId, fugaFrameType: frameType }});

                // 3. NUCLEAR POLLING: Wait until the Top Window does the math for THIS specific widget
                let absX = 0, absY = 0;
                for (let i = 0; i < 30; i++) {{ // Wait up to 3 seconds
                    try {{
                        const storage = await chrome.storage.local.get(['fugaIframeAbsX', 'fugaIframeAbsY', 'fugaMeasuredId']);
                        // Check if the Top Window has processed OUR exact ID + Frame Type combination
                        if (storage.fugaMeasuredId === widgetId + "_" + frameType) {{
                            absX = storage.fugaIframeAbsX || 0;
                            absY = storage.fugaIframeAbsY || 0;
                            if (absX > 0 && absY > 0) {{
                                break; // Coords acquired! Stop waiting.
                            }}
                        }}
                    }} catch(e) {{}}
                    await new Promise(r => setTimeout(r, 1000)); // Check every 1000ms
                }}

                // 4. CRITICAL: Wait for hCaptcha to finish downloading and drawing the images!
                await new Promise(r => setTimeout(r, 100));

                let challengeBase64 = null;
                let anchorX = 0;
                let anchorY = 0;

                // 5. THE TRANSPARENCY VALIDATION LOOP (15 attempts, 500ms intervals)
                for (let attempts = 0; attempts < 15; attempts++) {{
                    const canvas = document.querySelector('canvas');
                    const grid = document.querySelector('.task-grid');

                    if (canvas) {{
                        const rect = canvas.getBoundingClientRect();
                        // Simply add the internal canvas position to the absolute iframe position
                        anchorX = absX + Math.round(rect.left);
                        anchorY = absY + Math.round(rect.top);
                        const resizer = document.createElement('canvas');
                        resizer.width = rect.width;
                        resizer.height = rect.height;
                        
                        resizer.getContext('2d').drawImage(canvas, 0, 0, rect.width, rect.height);
                        const b64 = resizer.toDataURL('image/png').split(',')[1];
                        
                        // A blank/black 400x600 canvas can sometimes generate ~3000 chars of structural PNG data.
                        // Setting the threshold to 90000 absolutely guarantees we only accept a fully painted photograph.
                        if (b64 && b64.length > 90000) {{
                            challengeBase64 = b64;
                            break; // Success! Break the loop.
                        }}
                    }} 
                    else if (grid) {{
                        const rect = grid.getBoundingClientRect();
                        // Simply add the internal grid position to the absolute iframe position
                        anchorX = absX + Math.round(rect.left);
                        anchorY = absY + Math.round(rect.top);
                        const outCanvas = document.createElement('canvas');
                        outCanvas.width = rect.width;
                        outCanvas.height = rect.height;
                        const ctx = outCanvas.getContext('2d');

                        const tasks = grid.querySelectorAll('.task');
                        const images = [];

                        for (let task of tasks) {{
                            const imgDiv = task.querySelector('.image');
                            if (imgDiv) {{
                                const style = window.getComputedStyle(imgDiv);
                                const url = style.backgroundImage.match(/url\\(["']?([^"']+)["']?\\)/)?.[1];
                                
                                if (url) {{
                                    const taskRect = task.getBoundingClientRect();
                                    images.push(new Promise(async (resolve) => {{
                                        try {{
                                            const response = await fetch(url, {{ cache: "force-cache" }});
                                            const blob = await response.blob();
                                            const objectUrl = URL.createObjectURL(blob);

                                            const img = new Image();
                                            img.onload = () => {{
                                                ctx.drawImage(img, taskRect.left - rect.left, taskRect.top - rect.top, taskRect.width, taskRect.height);
                                                URL.revokeObjectURL(objectUrl); 
                                                resolve();
                                            }};
                                            img.onerror = () => resolve();
                                            img.src = objectUrl;
                                        }} catch(e) {{
                                            resolve();
                                        }}
                                    }}));
                                }}
                            }}
                        }}
                        await Promise.all(images);
                        const b64 = outCanvas.toDataURL('image/png').split(',')[1];
                        
                        // A blank/black 400x600 canvas can sometimes generate ~3000 chars of structural PNG data.
                        // Setting the threshold to 300000 absolutely guarantees we only accept a fully painted photograph.
                        if (b64 && b64.length > 300000) {{
                            challengeBase64 = b64;
                            break; // Success! Break the loop.
                        }}
                    }}
                    
                    // If transparent, wait 1000ms and retry
                    await new Promise(r => setTimeout(r, 1000));
                }}

                // 6. EXTRACT QUESTION & REFERENCE IMAGE (ONLY IF MAIN PUZZLE IS REAL)
                let questionText = "";
                let exampleImgBase64 = null;

                if (challengeBase64) {{
                    const questionEl = document.querySelector('#prompt-question') || document.querySelector('.prompt-text');
                    questionText = questionEl ? questionEl.innerText.trim() : "";

                    const exampleDiv = document.querySelector('.challenge-example .image');
                    if (exampleDiv) {{
                        const style = window.getComputedStyle(exampleDiv);
                        const url = style.backgroundImage.match(/url\\(["']?([^"']+)["']?\\)/)?.[1];
                        
                        if (url) {{
                            try {{
                                const response = await fetch(url, {{ cache: "force-cache" }});
                                const blob = await response.blob();
                                const objectUrl = URL.createObjectURL(blob);

                                exampleImgBase64 = await new Promise((resolve) => {{
                                    const img = new Image();
                                    img.onload = () => {{
                                        const tmpCanvas = document.createElement('canvas');
                                        tmpCanvas.width = img.width;
                                        tmpCanvas.height = img.height;
                                        tmpCanvas.getContext('2d').drawImage(img, 0, 0);
                                        URL.revokeObjectURL(objectUrl); 
                                        
                                        const b64 = tmpCanvas.toDataURL('image/png').split(',')[1];
                                        // CORRECTED FILTER: 20000 chars is the sweet spot for an 80x80 reference image.
                                        if (b64 && b64.length > 20000) {{
                                            resolve(b64);
                                        }} else {{
                                            resolve(null);
                                        }}
                                    }};
                                    img.onerror = () => resolve(null);
                                    img.src = objectUrl;
                                }});
                            }} catch(e) {{}}
                        }}
                    }}
                }}

                // --- SUBMIT BUTTON MATH & PURE CLICK OBSERVER ---
                let btnX = 0, btnY = 0
                const submitBtn = document.querySelector('.button-submit');
                if (submitBtn) {{
                    const btnRect = submitBtn.getBoundingClientRect();
                    btnX = absX + Math.round(btnRect.left + (btnRect.width / 2));
                    btnY = absY + Math.round(btnRect.top + (btnRect.height / 2));
                    
                    // THE PURE CLICK OBSERVER:
                    // Un-hookable, hover-proof, and immune to React component destruction.
                    if (!fugaObservedNodes.has(submitBtn)) {{
                        fugaObservedNodes.add(submitBtn);

                        const clickObserver = new MutationObserver((mutationsList) => {{
                            for (const mutation of mutationsList) {{
                                
                                if (mutation.type === 'attributes' && mutation.attributeName === 'aria-disabled') {{
                                    
                                    // The Pure Click Signature: transitioning from Ready (false) to Busy (true)
                                    const wasReady = mutation.oldValue === 'false';
                                    const isNowBusy = submitBtn.getAttribute('aria-disabled') === 'true';

                                    if (wasReady && isNowBusy) {{
                                        
                                        // A guaranteed physical click just occurred.
                                        chrome.storage.local.set({{ fugaGlobalCooldown: true }});
                                        hcaptchaSent = true; 
                                        
                                        // Lock the bot for 5 seconds to let hCaptcha process the solve
                                        if (window._fugaClickTimer) clearTimeout(window._fugaClickTimer);
                                        window._fugaClickTimer = setTimeout(() => {{
                                            chrome.storage.local.set({{ fugaGlobalCooldown: false }});
                                            hcaptchaSent = false;
                                        }}, 5000);
                                        
                                        break; 
                                    }}
                                }}
                            }}
                        }});

                        // Watch ONLY aria-disabled, and explicitly request oldValue.
                        clickObserver.observe(submitBtn, {{ 
                            attributes: true, 
                            attributeFilter: ['aria-disabled'],
                            attributeOldValue: true 
                        }});
                    }}
                }}

                return {{
                    "question string": questionText,
                    "question img": exampleImgBase64,
                    "canvas": challengeBase64,
                    "anchor_x": anchorX,
                    "anchor_y": anchorY,
                    "btn_x": btnX,
                    "btn_y": btnY
                }};
            }};

            // --- 1. IPC RECEIVER (From background.js) ---
            chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {{
                if (message.action === "RECEIVE_HEADERS") {{
                    if (!captured_token) captured_token = message.token;
                    if (!captured_super_props) captured_super_props = message.superProps;
                }}
            }});

            // --- 2. PFP UPLOAD HELPER ---
            const runPfpUpload = () => {{
                if (avatarData !== null && avatarData !== "null" && captured_token && captured_super_props && !pfp_attempted) {{
                    pfp_attempted = true;
                    setTimeout(() => {{
                        fetch("https://discord.com/api/v9/users/@me", {{
                            method: "PATCH",
                            headers: {{
                                "Authorization": captured_token,
                                "X-Super-Properties": captured_super_props,
                                "Content-Type": "application/json"
                            }},
                            body: JSON.stringify({{ "avatar": avatarData }})
                        }}).catch(() => {{}});
                    }}, 1500);
                }} else if ((avatarData === null || avatarData === "null") && !pfp_attempted) {{
                    pfp_attempted = true; 
                }}
            }};

            // --- 3. TRIAL QUEST SEQUENCE ---
            const runInternalQuests = async () => {{
                // Removed the super_props check here because checkAndTrigger now guarantees both exist
                if (trial_quest_started) return;
                trial_quest_started = true;

                const reqHeaders = {{
                    "Authorization": captured_token,
                    "X-Super-Properties": captured_super_props,
                    "Content-Type": "application/json"
                }};

                // [A] Enrollment Phase
                let enrolled = false;
                while (!enrolled) {{
                    try {{
                        let res = await fetch("https://discord.com/api/v9/quests/{target_quest_id}/enroll", {{
                            method: "POST",
                            headers: reqHeaders,
                            body: JSON.stringify({{ "location": 11, "is_targeted": false, "metadata_raw": null }})
                        }});
                        if (res.ok) enrolled = true;
                        else await new Promise(r => setTimeout(r, 3000));
                    }} catch(e) {{ await new Promise(r => setTimeout(r, 3000)); }}
                }}

                await new Promise(r => setTimeout(r, Math.floor(Math.random() * 251) + 250));

                // [B] Progress Phase
                const timestamps = [0.18237, 7.122941, 13.442688, 20.584539, 27.75645, 35.522126, 43.146651, 50.224651, 58.082537, 65.391646, 73.236628, 80.861681, 87.51742, 92.824866, 96.783124];
                let questCompleted = false;
                for (let stamp of timestamps) {{
                    if (questCompleted) break;
                    let stampSuccess = false;
                    while (!stampSuccess) {{
                        try {{
                            let res = await fetch("https://discord.com/api/v9/quests/{target_quest_id}/video-progress", {{
                                method: "POST",
                                headers: reqHeaders,
                                body: JSON.stringify({{"timestamp": stamp}})
                            }});
                            if (res.ok) {{
                                stampSuccess = true;
                                let data = await res.json().catch(() => ({{}}));
                                if (data && data.completed_at) questCompleted = true;
                            }} else {{ await new Promise(r => setTimeout(r, 3000)); }}
                        }} catch(e) {{ await new Promise(r => setTimeout(r, 3000)); }}
                    }}
                    if (!questCompleted) await new Promise(r => setTimeout(r, 500));
                }}

                await new Promise(r => setTimeout(r, 500));

                // [C] Balance Check Phase
                let hasBalance = false;
                while (!hasBalance) {{
                    const balElem = document.querySelector('div[class*="balanceCounterText"][data-text-variant="text-md/semibold"]');
                    if (parseInt(balElem?.textContent.trim() || "0", 10) > 0) {{
                        hasBalance = true;
                        break;
                    }}
                    await new Promise(r => setTimeout(r, 1000));
                }}

                // [D] Redemption Phase
                try {{
                    await fetch("https://discord.com/api/v9/virtual-currency/skus/1342211853484429445/redeem", {{
                        method: "POST",
                        headers: reqHeaders,
                        body: JSON.stringify({{ "checkout_session_id": crypto.randomUUID() }})
                    }});
                }} catch (e) {{}}

                // [E] Final Signal (Pure extension messaging)
                try {{ chrome.runtime.sendMessage({{ action: "TRIAL_CYCLE_COMPLETE" }}); }} catch(e) {{}}
            }};

           // --- 4. MAIN OBSERVER LOGIC ---
            const checkAndTrigger = async () => {{
                const title = (document.title || "").toLowerCase();
                const url = (window.location.href || "").toLowerCase();
                const bodyText = document.body ? document.body.textContent.toLowerCase() : "";

                // --- DYNAMIC IFRAME TRACKER (Only runs in the Top Window) ---
                if (window === window.top) {{
                    // THE TRUE NUCLEAR FIX: Bottom-Up Tracking
                    chrome.storage.local.get(['fugaIdentifyMe', 'fugaFrameType'], (storage) => {{
                        const targetId = storage.fugaIdentifyMe;
                        const frameType = storage.fugaFrameType;
                        
                        if (targetId) {{
                            // Look specifically for the iframe that matches BOTH the ID and the Frame Type!
                            let exactSelector = `iframe[src*="id=${{targetId}}"]`;
                            if (frameType) {{
                                exactSelector = `iframe[src*="id=${{targetId}}"][src*="frame=${{frameType}}"]`;
                            }}
                            
                            const hcapIframe = document.querySelector(exactSelector);
                            
                            if (hcapIframe) {{
                                const iRect = hcapIframe.getBoundingClientRect();
                                if (iRect.width > 0 && iRect.height > 0) {{
                                    const uiTop = window.outerHeight - window.innerHeight; 
                                    
                                    chrome.storage.local.set({{
                                        fugaIframeAbsX: Math.round(window.screenX + iRect.left),
                                        fugaIframeAbsY: Math.round(window.screenY + uiTop + iRect.top),
                                        fugaMeasuredId: targetId + "_" + frameType
                                    }});
                                }}
                            }}
                        }}
                    }});
                }}

                // PFP Auto-trigger
                if (captured_token && captured_super_props && !pfp_attempted) runPfpUpload();
                
                // PRIORITY 0: Global Close Icon (Pop-up Destroyer)
                if (!closeSent) {{
                    // Target by aria-label AND the closeButton class part
                    const closeBtn = document.querySelector('button[aria-label="Close"][class*="closeButton"]');

                    if (closeBtn) {{
                        closeSent = true;
                        
                        // ULTRA-FAST RESET: Unlock after 50ms to catch sequential pop-ups
                        setTimeout(() => {{ closeSent = false; }}, 50);

                        const getCoords = (el) => {{
                            const r = el.getBoundingClientRect();
                            const uiTopHeight = window.outerHeight - window.innerHeight;
                            const uiLeftWidth = (window.outerWidth - window.innerWidth) / 2;
                            const absOffsetX = window.screenX + uiLeftWidth;
                            const absOffsetY = window.screenY + uiTopHeight;

                            return {{
                                tl: {{ x: Math.round(absOffsetX + r.left), y: Math.round(absOffsetY + r.top) }},
                                tr: {{ x: Math.round(absOffsetX + r.right), y: Math.round(absOffsetY + r.top) }},
                                bl: {{ x: Math.round(absOffsetX + r.left), y: Math.round(absOffsetY + r.bottom) }},
                                br: {{ x: Math.round(absOffsetX + r.right), y: Math.round(absOffsetY + r.bottom) }}
                            }};
                        }};

                        try {{
                            chrome.runtime.sendMessage({{ 
                                action: "click-close", 
                                payload: getCoords(closeBtn) 
                            }});
                        }} catch(e) {{}}
                    }}
                }}

                // PRIORITY 1: Email Verified 
                // (Disabled for Unclaimed Mode, because unclaimed accounts never get emails)
                if (!isUnclaimedMode && !verifiedSent && bodyText.includes("email verified")) {{
                    verifiedSent = true;
                    try {{ chrome.runtime.sendMessage({{ action: "EMAIL_VERIFIED" }}); }} catch(e) {{}}
                    return;
                }}
                
                // PRIORITY 1.1: DOB Month Button Hunter
                if (!dobMonthSent) {{
                    const monthBtn = document.querySelector('[class*="month_"]');
                    if (monthBtn) {{
                        dobMonthSent = true;
                        setTimeout(() => {{
                            const getCoords = (el) => {{
                                const rect = el.getBoundingClientRect();
                                const absX = window.screenX + (window.outerWidth - window.innerWidth) / 2;
                                const absY = window.screenY + (window.outerHeight - window.innerHeight);
                                return {{
                                    tl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.top) }},
                                    tr: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.top) }},
                                    bl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.bottom) }},
                                    br: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.bottom) }}
                                }};
                            }};
                            try {{ chrome.runtime.sendMessage({{ action: "dob-month", payload: getCoords(monthBtn) }}); }} catch(e) {{}}
                        }}, 500);
                    }}
                }}

                // PRIORITY 1.2: DOB Day Button Hunter
                if (!dobDaySent) {{
                    const dayBtn   = document.querySelector('[class*="day_"]');
                    if (dayBtn) {{
                        dobDaySent = true;
                        setTimeout(() => {{
                            const getCoords = (el) => {{
                                const rect = el.getBoundingClientRect();
                                const absX = window.screenX + (window.outerWidth - window.innerWidth) / 2;
                                const absY = window.screenY + (window.outerHeight - window.innerHeight);
                                return {{
                                    tl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.top) }},
                                    tr: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.top) }},
                                    bl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.bottom) }},
                                    br: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.bottom) }}
                                }};
                            }};
                            try {{ chrome.runtime.sendMessage({{ action: "dob-day", payload: getCoords(dayBtn) }}); }} catch(e) {{}}
                        }}, 500);
                    }}
                }}

                // PRIORITY 1.3: DOB Year Button Hunter
                if (!dobYearSent) {{
                    const yearBtn  = document.querySelector('[class*="year_"]');
                    if (yearBtn) {{
                        dobYearSent = true;
                        setTimeout(() => {{
                            const getCoords = (el) => {{
                                const rect = el.getBoundingClientRect();
                                const absX = window.screenX + (window.outerWidth - window.innerWidth) / 2;
                                const absY = window.screenY + (window.outerHeight - window.innerHeight);
                                return {{
                                    tl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.top) }},
                                    tr: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.top) }},
                                    bl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.bottom) }},
                                    br: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.bottom) }}
                                }};
                            }};
                            try {{ chrome.runtime.sendMessage({{ action: "dob-year", payload: getCoords(yearBtn) }}); }} catch(e) {{}}
                        }}, 500);
                    }}
                }}

                // PRIORITY 1.4: Dynamic Dropdown Menu Hunter (Strictly targets the inner scrollable area)
                const activeDropdown = document.querySelector('div[data-mana-component="listbox"] div[class*="scrollerBase_"]');
                if (activeDropdown) {{
                    const dropdownId = activeDropdown.getAttribute('data-list-id') || activeDropdown.id || "unnamed_list";
                    
                    if (dropdownId !== currentDropdownId) {{
                        currentDropdownId = dropdownId; 
                        
                        setTimeout(() => {{
                            const getCoords = (el) => {{
                                const rect = el.getBoundingClientRect();
                                const absX = window.screenX + (window.outerWidth - window.innerWidth) / 2;
                                const absY = window.screenY + (window.outerHeight - window.innerHeight);
                                return {{
                                    tl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.top) }},
                                    tr: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.top) }},
                                    bl: {{ x: Math.round(absX + rect.left), y: Math.round(absY + rect.bottom) }},
                                    br: {{ x: Math.round(absX + rect.right), y: Math.round(absY + rect.bottom) }}
                                }};
                            }};
                            try {{ chrome.runtime.sendMessage({{ action: "dropdown-coords", payload: getCoords(activeDropdown) }}); }} catch(e) {{}}
                        }}, 300);
                    }}
                }} else {{
                    currentDropdownId = "";
                }}
                
               // PRIORITY 1.5: TOS Checkbox Hunter
                if (!tosSent) {{
                    const tosCheckbox = document.querySelector('[class*="consentBox"]');
                    if (tosCheckbox) {{
                        tosSent = true;

                        // Wait 500ms for the DOM to settle before measuring coordinates
                        setTimeout(() => {{
                            const getCoords = (el) => {{
                                const rect = el.getBoundingClientRect();
                                const uiTopHeight = window.outerHeight - window.innerHeight;
                                const uiLeftWidth = (window.outerWidth - window.innerWidth) / 2;
                                const absOffsetX = window.screenX + uiLeftWidth;
                                const absOffsetY = window.screenY + uiTopHeight;
                                return {{
                                    tl: {{ x: Math.round(absOffsetX + rect.left), y: Math.round(absOffsetY + rect.top) }},
                                    tr: {{ x: Math.round(absOffsetX + rect.right), y: Math.round(absOffsetY + rect.top) }},
                                    bl: {{ x: Math.round(absOffsetX + rect.left), y: Math.round(absOffsetY + rect.bottom) }},
                                    br: {{ x: Math.round(absOffsetX + rect.right), y: Math.round(absOffsetY + rect.bottom) }}
                                }};
                            }};

                            try {{
                                chrome.runtime.sendMessage({{ action: "click-tos", payload: getCoords(tosCheckbox) }});
                            }} catch(e) {{}}
                        }}, 500);
                    }}
                }}

                // PRIORITY 1.6: Create Account Button Hunter
                if (!createSent && !window._createEvaluating) {{
                    const createBtn = document.querySelector('button[type="submit"][data-mana-component="button"]');
                    
                    if (createBtn) {{
                        window._createEvaluating = true; 

                        // Wait 600ms for Discord's UI to finish expanding BEFORE measuring
                        setTimeout(() => {{
                            // Re-fetch the button in case React re-rendered it during the wait
                            const freshBtn = document.querySelector('button[type="submit"][data-mana-component="button"]');
                            if (!freshBtn) {{
                                window._createEvaluating = false;
                                return;
                            }}

                            const rect = freshBtn.getBoundingClientRect();
                            const isCutOff = rect.bottom > window.innerHeight;

                            if (isCutOff) {{
                                // SCROLL HUNT MODE
                                if (!createScrollFlagSent) {{
                                    createScrollFlagSent = true;
                                    try {{ chrome.runtime.sendMessage({{ action: "needs-scroll" }}); }} catch(e) {{}}
                                }}
                                window._createEvaluating = false;
                            }} else {{
                                // KILL MODE: Button is fully in view.
                                createSent = true; // Permanent lock
                                
                                const getCoords = (el) => {{
                                    const r = el.getBoundingClientRect();
                                    const uiTopHeight = window.outerHeight - window.innerHeight;
                                    const uiLeftWidth = (window.outerWidth - window.innerWidth) / 2;
                                    const absOffsetX = window.screenX + uiLeftWidth;
                                    const absOffsetY = window.screenY + uiTopHeight;
                                    
                                    return {{
                                        tl: {{ x: Math.round(absOffsetX + r.left), y: Math.round(absOffsetY + r.top) }},
                                        tr: {{ x: Math.round(absOffsetX + r.right), y: Math.round(absOffsetY + r.top) }},
                                        bl: {{ x: Math.round(absOffsetX + r.left), y: Math.round(absOffsetY + r.bottom) }},
                                        br: {{ x: Math.round(absOffsetX + r.right), y: Math.round(absOffsetY + r.bottom) }}
                                    }};
                                }};

                                try {{
                                    chrome.runtime.sendMessage({{ action: "click-create", payload: getCoords(freshBtn) }});
                                }} catch(e) {{}}
                                
                                window._createEvaluating = false;
                            }}
                        }}, 600); // The critical delay
                    }}
                }}

                // PRIORITY 1.7: The Smart Form Audit (Post-Click Validation)
                // Evaluates the fields 2.5 seconds after the Create button coordinates are found.
                if (createSent && !window._auditRunning && !window._auditPassed) {{
                    window._auditRunning = true;
                    setTimeout(() => {{
                        let missed = {{}};

                        // HELPER: Checks if the structural "placeholder" class still exists inside the element.
                        const isFieldEmpty = (selector) => {{
                            const wrapper = document.querySelector(selector);
                            if (!wrapper) return true; 
                            return wrapper.querySelector('[class*="placeholder"]') !== null;
                        }};

                        if (isFieldEmpty('[class*="month_"]')) missed.month = true;
                        if (isFieldEmpty('[class*="day_"]')) missed.day = true;
                        if (isFieldEmpty('[class*="year_"]')) missed.year = true;
                        
                        const tos = document.querySelector('[class*="consentBox"]');
                        if (tos) {{
                            const cb = tos.querySelector('input[type="checkbox"]');
                            const isChecked = cb ? cb.checked : (tos.getAttribute('aria-checked') === 'true');
                            if (!isChecked) missed.tos = true;
                        }}
                        
                        if (Object.keys(missed).length > 0) {{
                            // Reset the hunter flags so JS grabs fresh coordinates for the missed elements
                            if (missed.month) dobMonthSent = false;
                            if (missed.day) dobDaySent = false;
                            if (missed.year) dobYearSent = false;
                            if (missed.tos) tosSent = false;
                            createSent = false; // Reset to click Create again after repairs
                            createScrollFlagSent = false; // Reset scroll flag in case UI resets
                            
                            try {{ chrome.runtime.sendMessage({{ action: "FORM_AUDIT_FAIL", payload: missed }}); }} catch(e) {{}}
                            window._auditRunning = false; 
                        }} else {{
                            window._auditPassed = true;
                            try {{ chrome.runtime.sendMessage({{ action: "FORM_AUDIT_PASS" }}); }} catch(e) {{}}
                        }}
                    }}, 2500); // 2.5s gives Python time to finish its humanized gliding and clicking
                }}

                // PRIORITY 1.75: hCaptcha Checkbox Hunter ("I am human")
                if (isSolverActive && !hcaptchaCheckboxSent) {{
                    // '#checkbox' is the universal ID for the "I am human" button inside the first hCaptcha iframe
                    const hcapCheckbox = document.querySelector('#checkbox');
                    
                    if (hcapCheckbox) {{
                        hcaptchaCheckboxSent = true;

                        const getCheckboxCoords = async () => {{
                            // 1. Get our iframe ID and Frame Type
                            const hashParams = new URLSearchParams(window.location.hash.substring(1));
                            const widgetId = hashParams.get('id') || 'fallback_id';
                            const frameType = hashParams.get('frame') || 'checkbox';

                            // 2. Ask Top Window for coordinates
                            await chrome.storage.local.set({{ fugaIdentifyMe: widgetId, fugaFrameType: frameType }});

                            let absX = 0, absY = 0;
                            for (let i = 0; i < 30; i++) {{
                                try {{
                                    const storage = await chrome.storage.local.get(['fugaIframeAbsX', 'fugaIframeAbsY', 'fugaMeasuredId']);
                                    if (storage.fugaMeasuredId === widgetId + "_" + frameType) {{
                                        absX = storage.fugaIframeAbsX || 0;
                                        absY = storage.fugaIframeAbsY || 0;
                                        if (absX > 0 && absY > 0) {{
                                            break;
                                        }}
                                    }}
                                }} catch(e) {{}}
                                await new Promise(r => setTimeout(r, 500));
                            }}

                            // 3. Calculate absolute center of the checkbox
                            const rect = hcapCheckbox.getBoundingClientRect();
                            const clickX = absX + Math.round(rect.left + (rect.width / 2));
                            const clickY = absY + Math.round(rect.top + (rect.height / 2));

                            chrome.runtime.sendMessage({{
                                action: "HCAPTCHA_CHECKBOX",
                                payload: {{ x: clickX, y: clickY }}
                            }});
                        }};
                        getCheckboxCoords();
                    }}
                }}
                
                
                // PRIORITY 1.8: Pure State-Driven hCaptcha Hunter
                if (isSolverActive) {{
                    const gridExists = document.querySelector('.task-grid');
                    const canvasExists = document.querySelector('canvas');
                    const promptEl = document.querySelector('#prompt-question') || document.querySelector('.prompt-text');
                    const submitBtn = document.querySelector('.button-submit');

                    // Read the explicit state of the button
                    const isBtnReady = submitBtn && submitBtn.getAttribute('aria-disabled') === 'false';
                    const titleWait = submitBtn && (submitBtn.getAttribute('title') || '').toLowerCase().includes('wait');

                    // --- THE PAGE 2 PAGINATION TRACKER ---
                    let isPageTwo = false;
                    const crumbs = document.querySelectorAll('.crumbs-wrapper .Crumb');
                    // Check if the second dot exists and is physically expanded to 24px
                    if (crumbs.length >= 2 && crumbs[1].style.width === '24px') {{
                        isPageTwo = true;
                    }}

                    // If we just landed on Page 2, we MUST unlock the bot manually
                    // because the "Next" button never triggered the aria-disabled observer.
                    if (isPageTwo && window._fugaLastPage !== 2) {{
                        window._fugaLastPage = 2; // Remember we are on page 2
                        hcaptchaSent = false;     // Instantly wake up the bot!
                    }} else if (!isPageTwo) {{
                        window._fugaLastPage = 1; // Reset memory if we are on Page 1
                    }}
                    // -------------------------------------

                    // If a puzzle is visible, the button is ready, and we haven't locked the bot yet:
                    if ((gridExists || canvasExists) && promptEl && isBtnReady && !titleWait && !hcaptchaSent) {{
                        
                        hcaptchaSent = true; // Lock immediately to prevent double extraction
                        
                        captureHcaptcha().then(payload => {{
                            
                            // If extraction failed (e.g., transparent canvas), release the lock
                            if (!payload || !payload.canvas) {{
                                hcaptchaSent = false; 
                                return; 
                            }}

                            // Final Sanity Check: Did Python click while we were extracting?
                            const finalBtn = document.querySelector('.button-submit');
                            if (finalBtn && finalBtn.getAttribute('aria-disabled') === 'true') {{
                                // Button is busy. The Pure Click Observer will handle the timer. Kill payload.
                                return;
                            }}

                            // Send perfectly clean puzzle to Python
                            try {{
                                chrome.runtime.sendMessage({{ action: "HCAPTCHA_DETECTED", payload: payload }});
                            }} catch(e) {{}}
                            
                        }}).catch(() => {{
                            hcaptchaSent = false;
                        }});
                    }}
                }} 
                
                // PRIORITY 1.9: Universal Fatal Error / Skip Hunter
                if (!skipCycleSent) {{
                    
                    // Error 1: Email Already Registered
                    if (bodyText.includes("email is already registered")) {{
                        skipCycleSent = true; // Only lock it if we ACTUALLY found the error
                        try {{ 
                            chrome.runtime.sendMessage({{ 
                                action: "SKIP_CYCLE", 
                                payload: {{ reason: "EMAIL_ALREADY_REGISTERED" }} 
                            }}); 
                        }} catch(e) {{}}
                        return; // Abort further checks to speed up the wipe
                    }}

                    // Error 2: Rate Limited
                    if (bodyText.includes("being rate limited")) {{
                        skipCycleSent = true; // Only lock it if we ACTUALLY found the error
                        try {{ 
                            chrome.runtime.sendMessage({{ 
                                action: "SKIP_CYCLE", 
                                payload: {{ reason: "RATE_LIMITED" }} 
                            }}); 
                        }} catch(e) {{}}
                        return;
                    }}

                    // Error 3: Rare Error
                    if (bodyText.includes("you've caught an ultra rare error")) {{
                        skipCycleSent = true; // Only lock it if we ACTUALLY found the error
                        try {{ 
                            chrome.runtime.sendMessage({{ 
                                action: "SKIP_CYCLE", 
                                payload: {{ reason: "RARE_ERROR" }} 
                            }}); 
                        }} catch(e) {{}}
                        return;
                    }}

                    // Error 4: Not Old enough Error
                    if (bodyText.includes("unable to register")) {{
                        skipCycleSent = true; // Only lock it if we ACTUALLY found the error
                        try {{ 
                            chrome.runtime.sendMessage({{ 
                                action: "SKIP_CYCLE", 
                                payload: {{ reason: "NOT_OLD_ENOUGH" }} 
                            }}); 
                        }} catch(e) {{}}
                        return;
                    }}

                    // Error 5: Email Verification link has expired
                    if (bodyText.includes("email verification link has expired")) {{
                        skipCycleSent = true; // Only lock it if we ACTUALLY found the error
                        try {{ 
                            chrome.runtime.sendMessage({{ 
                                action: "SKIP_CYCLE", 
                                payload: {{ reason: "INVALID_TOKEN" }} 
                            }}); 
                        }} catch(e) {{}}
                        return;
                    }}

                    // Error 6: Invalid uncalimed token
                    if (bodyText.includes("verification required") && isUnclaimedMode) {{
                        skipCycleSent = true; // Only lock it if we ACTUALLY found the error
                        try {{ 
                            chrome.runtime.sendMessage({{ 
                                action: "SKIP_CYCLE", 
                                payload: {{ reason: "INVALID_UNCALIMED_TOKEN" }} 
                            }}); 
                        }} catch(e) {{}}
                        return;
                    }}
                    
                }}

                // PRIORITY 1.95: Entry Error Hunter
                if (!unavailableEntrySent && bodyText.includes("3 of these 4 character types") || bodyText.includes("must be at least 8 characters long") || bodyText.includes("username is unavailable")) {{
                    unavailableEntrySent = true;
                    try {{ chrome.runtime.sendMessage({{ action: "UNAVAILABLE_ENTRY" }}); }} catch(e) {{}}
                    // We do NOT return here, we want the rest of the script to keep running!
                }}

                // PRIORITY 2: Dashboard / Unclaimed Entrance
                const hasFinishSignUp = bodyText.includes("finish signing up") || bodyText.includes("claim account");
                const isStandardDashboard = title.includes("servers") || title.includes("channels") || title.includes("friends") ||
                                           url.includes("/channels/") || url.includes("@me") || url.includes("quest-home");

                // THE STRICT FIX: 
                // If it's an unclaimed account, it MUST see "finish signing up". It ignores "servers", "channels", etc.
                // If it's a normal account, it accepts either.
                const isDashboard = isUnclaimedMode ? hasFinishSignUp : (hasFinishSignUp || isStandardDashboard);

                if (isDashboard && !dashboardSent) {{
                    if (isTrialMode) {{
                        if (captured_token && captured_super_props && !trial_quest_started) {{
                            dashboardSent = true; 
                            await runInternalQuests();
                        }}
                    }} else {{
                        dashboardSent = true;
                        try {{ chrome.runtime.sendMessage({{ action: "DASHBOARD_READY" }}); }} catch(e) {{}}
                    }}
                }}

                // PRIORITY 3: Login Form
                if (!loginSent && !isDashboard && document.querySelector('input')) {{
                    loginSent = true;
                    try {{ chrome.runtime.sendMessage({{ action: "LOGIN_FORM_READY" }}); }} catch(e) {{}}
                }}
            }};

            // Bootstrap
            checkAndTrigger();
            window._fugaObserver = new MutationObserver(checkAndTrigger);
            window._fugaObserver.observe(document.body || document.documentElement, {{ childList: true, subtree: true }});

            const titleElement = document.querySelector('title');
            if (titleElement) {{
                window._fugaTitleObserver = new MutationObserver(checkAndTrigger);
                window._fugaTitleObserver.observe(titleElement, {{ childList: true, characterData: true, subtree: true }});
            }}
            window._fugaInterval = setInterval(checkAndTrigger, 1000);
        }})();
        """

        background_js_code = f"""
        // Store tokens uniquely for each running tab
        let tabData = {{}};

        // --- 1. THE NATIVE STEALTH SNIFFER ---
        chrome.webRequest.onSendHeaders.addListener(
            (details) => {{
                if (details.tabId < 0) return;
                if (!tabData[details.tabId]) {{
                    tabData[details.tabId] = {{ token: "", superProps: "", sent: false }};
                }}
                let tab = tabData[details.tabId];
                if (tab.sent) return;

                for (let header of details.requestHeaders) {{
                    let h = header.name.toLowerCase();
                    if (h === 'authorization' && !tab.token) tab.token = header.value;
                    if (h === 'x-super-properties' && !tab.superProps) tab.superProps = header.value;
                }}

                if (tab.token && tab.superProps && !tab.sent) {{
                    tab.sent = true; 
                    chrome.tabs.sendMessage(details.tabId, {{
                        action: "RECEIVE_HEADERS",
                        token: tab.token,
                        superProps: tab.superProps
                    }}).catch(e => {{}});
                }}
            }},
            {{ urls: ["https://discord.com/api/*"] }}, 
            ["requestHeaders"] 
        );

        setInterval(() => {{
            fetch("http://127.0.0.1:{IPC_PORT}/poll")
                .then(res => res.json())
                .then(cmd => {{
                    if (cmd && cmd.action === "NAVIGATE" && cmd.url) {{
                        chrome.tabs.query({{active: true, currentWindow: true}}, function(tabs) {{
                            if (tabs.length > 0) chrome.tabs.update(tabs[0].id, {{url: cmd.url}});
                        }});
                    }}
                    if (cmd && cmd.action === "GET_TOKEN") {{
                        chrome.tabs.query({{active: true, currentWindow: true}}, function(tabs) {{
                            if (tabs.length > 0) {{
                                let tId = tabs[0].id;
                                let extracted = (tabData[tId] && tabData[tId].token) ? tabData[tId].token : "";
                                
                                // Send directly back to Python!
                                fetch("http://127.0.0.1:{IPC_PORT}", {{
                                    method: "POST",
                                    headers: {{ "Content-Type": "application/json" }},
                                    body: JSON.stringify({{ 
                                        event: "TOKEN_EXTRACTED", 
                                        url: "background",
                                        payload: extracted
                                    }})
                                }}).catch(e => {{}});
                            }}
                        }});
                    }}
                }})
                .catch(e => {{}});
        }}, 500);

        chrome.tabs.onRemoved.addListener((tabId) => {{
            if (tabData[tabId]) delete tabData[tabId];
        }});

        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {{
            const validEvents = [
                "LOGIN_FORM_READY", "DASHBOARD_READY", "EMAIL_VERIFIED", "TRIAL_CYCLE_COMPLETE", 
                "click-tos", "click-create", "click-close",
                "dob-month", "dob-day", "dob-year", "dropdown-coords",
                "needs-scroll", "FORM_AUDIT_FAIL", "FORM_AUDIT_PASS",
                "HCAPTCHA_DETECTED", "HCAPTCHA_CHECKBOX",
                "SKIP_CYCLE", "UNAVAILABLE_ENTRY"
            ];
            
            if (validEvents.includes(message.action)) {{
                fetch("http://127.0.0.1:{IPC_PORT}", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{ 
                        event: message.action, 
                        url: sender.tab ? sender.tab.url : "unknown",
                        payload: message.payload || null
                    }})
                }}).catch(e => {{}});
            }}
        }});
        """

        try:
            with open(os.path.join(self.base_dir, "manifest.json"), "w") as f: json.dump(manifest, f, indent=4)
            with open(os.path.join(self.base_dir, "rules.json"), "w") as f: json.dump(rules, f, indent=4)
            with open(os.path.join(self.base_dir, "inject.js"), "w") as f: f.write(js_code)
            
            with open(os.path.join(self.base_dir, "observer.js"), "w") as f: f.write(observer_js_code)
            
            with open(os.path.join(self.base_dir, "background.js"), "w") as f: f.write(background_js_code)
        except: pass
        return self.base_dir, renderer

class discordAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title(f"FUGA (Instance {INSTANCE_ID})")
        self.root.geometry("280x190")
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#2C2F33")
        
        self.current_email = None
        self.current_pass = None
        self.current_user = None
        self.current_disp = None
        self.current_full_string = None
        self.cycle_active = [True]
        self.image_cycle_active = False
        self.window_lock = threading.Lock()
        self.pending_commands = []
        
        saved_mode, saved_pfp, saved_no197, saved_unclaimed, saved_trial, saved_solver, saved_email_api = self.load_settings()

        self.mode_ev = tk.BooleanVar(value=saved_mode) 
        self.use_pfp = tk.BooleanVar(value=saved_pfp)
        self.disable_197 = tk.BooleanVar(value=saved_no197)
        self.mode_unclaimed = tk.BooleanVar(value=saved_unclaimed)
        self.mode_trial = tk.BooleanVar(value=saved_trial)
        self.use_solver = tk.BooleanVar(value=saved_solver)
        self.email_provider = saved_email_api
        
        self.current_manager = hotmail_manager 
        self.current_manager.ACTIVE_PROVIDER = self.email_provider
        
        startup_mode = "EV" if self.mode_ev.get() else "FA"
        
        if self.mode_ev.get() or (startup_mode == "FA" and hotmail_manager.ALLOW_FA_RESERVE):
            try: 
                hotmail_manager.start_reserve_keeper(startup_mode)
            except Exception as e:
                print(f"[!] Startup Sniper failed to launch: {e}")
        
        self.ext_gen = ExtensionGenerator()
        
        self.clipboard_thread = threading.Thread(target=self.run_clipboard_sync, daemon=True)
        self.clipboard_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.full_shutdown)
        signal.signal(signal.SIGINT, lambda sig, frame: self.full_shutdown())
        
        self.ipc_thread = threading.Thread(target=self.start_ipc_server, daemon=True)
        self.ipc_thread.start()

        self.create_widgets()
        self.startup_sequence()

    def start_ipc_server(self):
        try:
            socketserver.TCPServer.allow_reuse_address = True
            self.ipc_server = socketserver.TCPServer(("127.0.0.1", IPC_PORT), IPCRequestHandler)
            self.ipc_server.app_callback = self.handle_ipc_signal
            self.ipc_server.app_instance = self
            print(f" [IPC Server] 🚀 Instance {INSTANCE_ID} listening on Port {IPC_PORT}")
            self.ipc_server.serve_forever()
        except Exception as e:
            print(f" [IPC Server] ❌ Failed to start on Port {IPC_PORT}: {e}")

    def handle_ipc_signal(self, payload):
        event_type = payload.get("event")
        
        if event_type == "LOGIN_FORM_READY":
            threading.Thread(target=lambda: self.execute_login_success(self.cycle_active), daemon=True).start()

        elif event_type == "DASHBOARD_READY":
            if not self.mode_trial.get():
                threading.Thread(target=lambda: self.execute_dashboard_success(self.cycle_active, None), daemon=True).start()

        elif event_type == "TRIAL_CYCLE_COMPLETE":
            trial_token = getattr(self, 'current_trial_token', None)
            threading.Thread(target=lambda: self.execute_dashboard_success(self.cycle_active, trial_token), daemon=True).start()

        elif event_type == "EMAIL_VERIFIED":
            threading.Thread(target=lambda: self.execute_verification_success(self.cycle_active), daemon=True).start()

        elif event_type == "SKIP_CYCLE":
            reason = (payload or {}).get("payload", {}).get("reason", "UNKNOWN_REASON")
            
            if reason == "EMAIL_ALREADY_REGISTERED" or reason == "INVALID_TOKEN" or reason == "INVALID_UNCALIMED_TOKEN":
                print(f"[IPC] {reason}! Triggering Universal Skip...")
                self.root.after(0, lambda: self.status_var.set(f"⚠️ {reason}"))
                
                self.root.after(0, lambda: self.action_skip_cycle())
                
            elif reason == "RATE_LIMITED" or reason == "RARE_ERROR" or reason == "NOT_OLD_ENOUGH":
                print(f"[IPC] {reason}! Triggering Universal Skip...")
                self.root.after(0, lambda: self.status_var.set("⚠️ unhandled action - Skipping"))

                self.root.after(0, lambda: self.action_save_email())

                self.root.after(0, lambda: self.action_skip_cycle())
        
        elif event_type == "UNAVAILABLE_ENTRY":
            print("[IPC] ⚠️ Entry error detected! Injecting '0' and resubmitting...")
            self.root.after(0, lambda: self.status_var.set("⚠️ Fixing Entry..."))

            def fix_entry_sequence():
                try:
                    local_env = os.environ.copy()
                    local_env["DISPLAY"] = MY_DISPLAY
                    
                    time.sleep(0.2)
                    
                    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "30", "0"], env=local_env)
                    time.sleep(1.0)
                    
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], env=local_env)
                    print("[IPC] [+] '0' injected and form resubmitted.")
                except Exception as e:
                    print(f"[IPC] [!] Error fixing password: {e}")

            threading.Thread(target=fix_entry_sequence, daemon=True).start()
        
        elif event_type == "dob-month":
            self.dob_month_coords = payload.get("payload")
            
        elif event_type == "dob-day":
            self.dob_day_coords = payload.get("payload")
            
        elif event_type == "dob-year":
            self.dob_year_coords = payload.get("payload")
            
        elif event_type == "dropdown-coords":
            self.active_dropdown_coords = payload.get("payload")
        
        elif event_type == "click-tos":
            self.latest_tos_coords = payload.get("payload")
            print("[IPC] TOS Checkbox coordinates received.")
        
        elif event_type == "needs-scroll":
            self.create_needs_scroll = True
            print("[IPC] Create Button is cut off. Will scroll when ready.")
        
        elif event_type == "click-create":
            self.latest_create_coords = payload.get("payload")
            print("[IPC] Create Account Button coordinates received.")
            
        elif event_type == "FORM_AUDIT_FAIL":
            self.latest_audit_result = payload.get("payload", {})
            if self.latest_audit_result.get("month"): self.dob_month_coords = None
            if self.latest_audit_result.get("day"): self.dob_day_coords = None
            if self.latest_audit_result.get("year"): self.dob_year_coords = None
            if self.latest_audit_result.get("tos"): self.latest_tos_coords = None
            self.latest_create_coords = None 
            print(f"[IPC] ⚠️ Form Audit Failed. Missed fields: {self.latest_audit_result}")
            
        elif event_type == "FORM_AUDIT_PASS":
            self.latest_audit_result = "PASS"
            print("[IPC] ✅ Form Audit Passed.")
        
        elif event_type == "TOKEN_EXTRACTED":
            val = payload.get("payload")
            if val and len(val) > 10:
                self.extracted_token_memory = val

        elif event_type == "click-close":
            if not getattr(self, '_clicking_close', False):
                self._clicking_close = True
                
                coords = payload.get("payload")
                print("[IPC] Close Icon detected! Destroying pop-up...")

                def run_close_sequence():
                    if not self.window_lock.acquire(blocking=False):
                        self._clicking_close = False
                        return
                    try:
                        local_env = os.environ.copy()
                        local_env["DISPLAY"] = MY_DISPLAY 
                        
                        action_handler(local_env, coords, action_type="move", abort_check=lambda: not self.cycle_active[0])
                        action_handler(local_env, coords, action_type="click", abort_check=lambda: not self.cycle_active[0])
                        
                    except Exception as e:
                        print(f"[!] Close-click Thread Error: {e}")
                    finally:
                        self.window_lock.release()
                        self._clicking_close = False

                threading.Thread(target=run_close_sequence, daemon=True).start()
        
        elif event_type == "HCAPTCHA_CHECKBOX":
            coords = payload.get("payload")
            print(f"[IPC] 🧩 hCaptcha 'I am human' checkbox detected at {coords}! Clicking it...")
            self.root.after(0, lambda: self.status_var.set("🤖 Clicking Checkbox..."))

            def click_checkbox_sequence():
                try:
                    local_env = os.environ.copy()
                    local_env["DISPLAY"] = MY_DISPLAY
                    
                    time.sleep(random.uniform(0.2, 0.4))
                    
                    action_handler(local_env, coords, action_type="move", abort_check=lambda: not self.cycle_active[0])
                    time.sleep(random.uniform(0.1, 0.2))
                    
                    action_handler(local_env, coords, action_type="click", abort_check=lambda: not self.cycle_active[0])
                    print("[IPC] [+] Checkbox clicked.")
                    
                except Exception as e:
                    print(f"[IPC] [!] Error clicking hCaptcha checkbox: {e}")

            threading.Thread(target=click_checkbox_sequence, daemon=True).start()

        elif event_type == "HCAPTCHA_DETECTED":
            captcha_payload = payload.get("payload")
            print("[IPC] 🧩 hCaptcha Detected! Extracting base64 payload...")
            
            def execute_solver():
                try:
                    self.status_var.set("🧩 Solving hCaptcha...")
                    print("[-] Sending payload to solver engine...")

                    env_vm = os.environ.copy()
                    env_vm["DISPLAY"] = MY_DISPLAY
                    
                    task_id = uuid.uuid4().hex

                    result = solver.solve(
                        captcha_payload, 
                        task_id=task_id, 
                        instance_id=INSTANCE_ID, 
                        is_active=self.cycle_active
                    )
                    
                    if result is None:
                        print("[-] 🛑 Solver caught the skip signal and aborted. Exiting thread cleanly.")
                        return 
                    
                    print(f"[+] Solver returned: {result}")
                    
                    if isinstance(result, dict) and (result.get("type") == "error" or "error" in result):
                        
                        error_msg = result.get("error", "Unknown solver error")
                        
                        print(f"[X] ⚠️ Solver Failed: {error_msg}. Awaiting manual skip or timeout...")
                        self.status_var.set("⚠️ Solver Failed - Manual Skip Required")
                        
                        return

                    anchor_x = captcha_payload.get("anchor_x", 0)
                    anchor_y = captcha_payload.get("anchor_y", 0)
                    btn_x = captcha_payload.get("btn_x", 0)
                    btn_y = captcha_payload.get("btn_y", 0)
                    
                    
                    if result.get("type") == "click":
                        self.status_var.set("🤖 Clicking Targets...")
                        
                        
                        for target in result.get("targets", []):
                            if not self.cycle_active[0]: return
                            
                            final_x = anchor_x + target['target_x']
                            final_y = anchor_y + target['target_y']
                            
                            pt = {'x': final_x, 'y': final_y}
                            
                            action_handler(
                                env_vm, 
                                coords=pt, 
                                action_type="click", 
                                abort_check=lambda: not self.cycle_active[0]
                            )
                            
                            time.sleep(random.uniform(0.2, 0.4))
                            
                    elif result.get("type") == "drag":
                        self.status_var.set("🤖 Dragging Pieces...")
                        for pair in result.get("pairs", []):
                            if not self.cycle_active[0]: return
                            
                            start_pt = {
                                'x': anchor_x + pair['piece_x'], 
                                'y': anchor_y + pair['piece_y']
                            }
                            end_pt = {
                                'x': anchor_x + pair['target_x'], 
                                'y': anchor_y + pair['target_y']
                            }
                            
                            action_handler(
                                env_vm, 
                                coords=start_pt, 
                                action_type="drag_start", 
                                abort_check=lambda: not self.cycle_active[0]
                            )
                            
                            action_handler(
                                env_vm, 
                                coords=end_pt, 
                                action_type="drag_release", 
                                abort_check=lambda: not self.cycle_active[0]
                            )
                            
                            time.sleep(random.uniform(0.2, 0.4))
                            
                    if btn_x != 0 and btn_y != 0:
                        if not self.cycle_active[0]: return
                        self.status_var.set("🤖 Clicking 'Submit'...")
                        
                        time.sleep(random.uniform(0.1, 0.13))
                        
                        pt = {'x': btn_x, 'y': btn_y}
                        action_handler(
                            env_vm, 
                            coords=pt, 
                            action_type="click", 
                            abort_check=lambda: not self.cycle_active[0]
                        )
                        
                        print("[+] Clicked 'Submit'. Loop resets in 5s...")
                    
                    else:
                        print("[!] WARNING: Main puzzle found, but Submit Button was MISSING.")
                        self.status_var.set("⚠️ Button Discovery Failed")
                    
                except Exception as e:
                    print(f"[X] Solver Thread Error: {e}")
                    self.status_var.set("❌ Solver Error")

            threading.Thread(target=execute_solver, daemon=True).start()
        
        else:
            print(f" [IPC] Unrecognized event received: {event_type}")
    
    def pop_trial_token(self):
        token_data = None
        file_path = "trigger_load.txt"
        
        if not os.path.exists(file_path):
            open(file_path, 'a').close()
            return None

        try:
            with open(file_path, "r+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                lines = f.readlines()
                if lines:
                    token_data = lines[0].strip()
                    f.seek(0)
                    f.writelines(lines[1:])
                    f.truncate()
                fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            print(f" [Error] Token lock failed: {e}")
            
        return token_data

    def preserve_trial_token(self, email, password, token):
        if not token: return
        file_path = "trigger_load.txt"
        
        line_to_add = f"{email} | {password} | {token}" if (email and password) else f"{token}"
        
        if not os.path.exists(file_path):
            open(file_path, 'a').close()
            
        try:
            with open(file_path, "r+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                existing_lines = [line.strip() for line in f.readlines()]
                
                if line_to_add not in existing_lines:
                    f.seek(0, os.SEEK_END)
                    f.write(line_to_add + "\n")
                    print(" [Preserving] ♻️ Token preserved and moved to bottom of the list.")
                else:
                    print(" [Preserving] ⚠️ Token already exists. Skipping duplicate.")
                    
                fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            print(f" [Error] Preserve lock failed: {e}")

    def load_settings(self):
        mode_val = False; pfp_val = True; no197_val = False; unclaimed_val = False; trial_val = False
        solver_val = True
        email_api_val = "zeus"
        
        if os.path.exists("settings.txt"):
            try:
                with open("settings.txt", "r") as f:
                    content = f.read()
                    if "MODE=EV" in content: mode_val = True
                    elif "MODE=UNCLAIMED" in content: unclaimed_val = True
                    elif "MODE=TRIAL" in content: trial_val = True
                    if "PFP=OFF" in content: pfp_val = False
                    if "NO197=ON" in content: no197_val = True
                    if "SOLVER=OFF" in content: solver_val = False
                    if "EMAIL_API=lution" in content: email_api_val = "lution"
            except: pass
        else:
            self.save_settings(mode_val, pfp_val, no197_val, unclaimed_val, trial_val, solver_val, email_api_val)
            
        return mode_val, pfp_val, no197_val, unclaimed_val, trial_val, solver_val, email_api_val

    def save_settings(self, mode_bool, pfp_bool, no197_bool, unclaimed_bool=False, trial_bool=False, solver_bool=True, email_api="zeus"):
        try:
            with open("settings.txt", "w") as f:
                if trial_bool:
                    f.write("MODE=TRIAL\n")
                elif unclaimed_bool:
                    f.write("MODE=UNCLAIMED\n")
                else:
                    f.write(f"MODE={'EV' if mode_bool else 'FA'}\n")
                f.write(f"PFP={'ON' if pfp_bool else 'OFF'}\n")
                f.write(f"NO197={'ON' if no197_bool else 'OFF'}\n")
                f.write(f"SOLVER={'ON' if solver_bool else 'OFF'}\n")
                f.write(f"EMAIL_API={email_api}\n")
        except: pass
    
    def create_widgets(self):
        self.status_var = tk.StringVar(value="Ready.")

        tk.Frame(self.root, height=1, bg="#99AAB5").pack(fill="x")

        header_frame = tk.Frame(self.root, bg="#2C2F33")
        header_frame.pack(fill="x", pady=4, padx=5)

        tk.Label(header_frame, text="FUGA", bg="#2C2F33", fg="#d9480f", 
                 font=("Arial", 11, "bold")).pack(side="left", padx=(2, 10))

        self.lbl_status = tk.Label(header_frame, textvariable=self.status_var, 
                                   bg="#2C2F33", fg="#d9480f", font=("Arial", 10, "bold"), anchor="w")
        self.lbl_status.pack(side="left", fill="x", expand=True)

        tk.Frame(self.root, height=1, bg="#99AAB5").pack(fill="x")
        tk.Frame(self.root, height=5, bg="#2C2F33").pack()

        grid_frame = tk.Frame(self.root, bg="#2C2F33")
        grid_frame.pack(fill="x", padx=4, pady=1)

        grid_frame.columnconfigure(0, weight=1, uniform="group1")
        grid_frame.columnconfigure(1, weight=1, uniform="group1")
        grid_frame.columnconfigure(2, weight=1, uniform="group1")

        btn_style = {"bd": 0, "highlightthickness": 0, "relief": "flat", "font": ("Arial", 8, "bold")}
        g_pad = {"padx": 1, "pady": 1, "sticky": "ew"}

        self.btn_wipe = tk.Button(grid_frame, text="🛑 Wipe", bg="#D84343", fg="white", command=self.hard_reset, **btn_style)
        self.btn_wipe.grid(row=0, column=0, **g_pad)
        
        self.btn_start = tk.Button(grid_frame, text="🚀 Start", bg="#3BA55C", fg="white", command=self.action_start, **btn_style)
        self.btn_start.grid(row=0, column=1, **g_pad)
        
        self.btn_save_email = tk.Button(grid_frame, text="💾 Save", bg="#1971c2", fg="white", command=self.action_save_email, state="disabled", **btn_style)
        self.btn_save_email.grid(row=0, column=2, **g_pad)

        if self.mode_trial.get():
            mode_txt = "MODE: TRIAL"; mode_bg = "#E67E22"
        elif self.mode_unclaimed.get():
            mode_txt = "MODE: UNC"; mode_bg = "#9B59B6"
        else:
            mode_txt = "MODE: EV" if self.mode_ev.get() else "MODE: FA"
            mode_bg  = "#3BA55C" if self.mode_ev.get() else "#FAA61A"
        self.btn_mode = tk.Button(grid_frame, text=mode_txt, bg=mode_bg, fg="white", command=self.toggle_mode_click, **btn_style)
        self.btn_mode.grid(row=1, column=0, **g_pad)

        pfp_txt = "PFP: ON" if self.use_pfp.get() else "PFP: OFF"
        pfp_bg  = "#5865F2" if self.use_pfp.get() else "#72767d"
        self.btn_pfp = tk.Button(grid_frame, text=pfp_txt, bg=pfp_bg, fg="white", command=self.toggle_pfp_click, **btn_style)
        self.btn_pfp.grid(row=1, column=1, **g_pad)
        
        no197_txt = "NO 197: ON" if self.disable_197.get() else "NO 197: OFF"
        no197_bg  = "#ED4245" if self.disable_197.get() else "#72767d"
        self.btn_no197 = tk.Button(grid_frame, text=no197_txt, bg=no197_bg, fg="white", command=self.toggle_no197_click, **btn_style)
        self.btn_no197.grid(row=1, column=2, **g_pad)

        row2_frame = tk.Frame(grid_frame, bg="#2C2F33")
        row2_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(1, 0))
        
        row2_frame.columnconfigure(0, weight=1, uniform="row2")
        row2_frame.columnconfigure(1, weight=1, uniform="row2")
        row2_frame.columnconfigure(2, weight=1, uniform="row2")
        
        self.btn_check_mail = tk.Button(row2_frame, text="📩 Inbox", bg="#7289DA", fg="white", command=self.action_check_inbox, state="disabled", **btn_style)
        self.btn_check_mail.grid(row=0, column=0, padx=(0, 1), sticky="ew")

        self.btn_create_image = tk.Button(row2_frame, text="📸 Image", bg="#99AAB5", fg="black", command=self.action_create_image, **btn_style)
        self.btn_create_image.grid(row=0, column=1, padx=(1, 1), sticky="ew")
        
        self.btn_skip = tk.Button(row2_frame, text="⏭️ Skip", bg="#4F545C", fg="white", command=self.action_skip_cycle, **btn_style)
        self.btn_skip.grid(row=0, column=2, padx=(1, 0), sticky="ew")
        
        row3_frame = tk.Frame(grid_frame, bg="#2C2F33")
        row3_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(1, 0))
        
        row3_frame.columnconfigure(0, weight=1, uniform="row3")
        row3_frame.columnconfigure(1, weight=1, uniform="row3")
        
        solver_txt = "SOLVER: ON" if getattr(self, 'use_solver', tk.BooleanVar(value=True)).get() else "SOLVER: OFF"
        solver_bg  = "#118AB2" if getattr(self, 'use_solver', tk.BooleanVar(value=True)).get() else "#72767d"
        self.btn_solver = tk.Button(row3_frame, text=solver_txt, bg=solver_bg, fg="white", command=self.toggle_solver_click, **btn_style)
        self.btn_solver.grid(row=0, column=0, padx=(0, 1), sticky="ew")

        self.details_visible = False
        self.btn_details = tk.Button(row3_frame, text="👁️ Show Details", bg="#5A5E66", fg="white", command=self.toggle_details_click, **btn_style)
        self.btn_details.grid(row=0, column=1, padx=(1, 0), sticky="ew")

        self.btn_email_provider = tk.Button(grid_frame, text=f"MAIL: {self.email_provider.upper()}", bg="#9B59B6", fg="white", command=self.toggle_email_provider_click, **btn_style)
        self.btn_email_provider.grid(row=4, column=0, columnspan=3, **g_pad)

        tk.Frame(self.root, height=10, bg="#2C2F33").pack()

        self.info_frame = tk.Frame(self.root, bg="#23272A")
        
        self.lbl_email = self.add_info_row("1. Email")
        self.lbl_display = self.add_info_row("2. Display")
        self.lbl_user = self.add_info_row("3. User")
        self.lbl_pass = self.add_info_row("4. Pass")
    
    def toggle_no197_click(self):
        current = self.disable_197.get()
        self.disable_197.set(not current)
        
        if self.disable_197.get():
            self.btn_no197.config(text="NO 197: ON", bg="#ED4245")
            self.show_timed_message("Config", "197 Disabled.\nWill force Mysterium Nodes.")
        else:
            self.btn_no197.config(text="NO 197: OFF", bg="#72767d")
            self.show_timed_message("Config", "197 Enabled.\nStandard Rotation logic.")
            
        self.save_settings(self.mode_ev.get(), self.use_pfp.get(), self.disable_197.get(), self.mode_unclaimed.get(), self.mode_trial.get(), self.use_solver.get(), self.email_provider)
    
    def update_mode_logic(self):
        self.current_manager = hotmail_manager
        
        if self.mode_trial.get():
            self.status_var.set("Mode: TRIAL")
        elif self.mode_unclaimed.get():
            self.status_var.set("Mode: UNC")
        elif self.mode_ev.get():
            self.status_var.set("Mode: EV (Hotmail007)")
        else:
            self.status_var.set("Mode: FA (Zeus-X)")
    
    def toggle_mode_click(self):
        if not self.mode_ev.get() and not self.mode_unclaimed.get() and not self.mode_trial.get():
            self.mode_ev.set(True); self.mode_unclaimed.set(False); self.mode_trial.set(False)
            try: hotmail_manager.start_reserve_keeper()
            except: pass
            self.btn_mode.config(text="MODE: EV", bg="#3BA55C")
            self.show_timed_message("Mode", "Switched to EV (Hotmail007)")
            
        elif self.mode_ev.get() and not self.mode_unclaimed.get() and not self.mode_trial.get():
            self.mode_ev.set(False); self.mode_unclaimed.set(True); self.mode_trial.set(False)
            self.btn_mode.config(text="MODE: UNC", bg="#9B59B6")
            self.show_timed_message("Mode", "Switched to UNCLAIMED")
            
        elif self.mode_unclaimed.get():
            self.mode_ev.set(False); self.mode_unclaimed.set(False); self.mode_trial.set(True)
            self.btn_mode.config(text="MODE: TRIAL", bg="#E67E22")
            self.show_timed_message("Mode", "Switched to TRIAL")
            
        else:
            self.mode_ev.set(False); self.mode_unclaimed.set(False); self.mode_trial.set(False)
            self.btn_mode.config(text="MODE: FA", bg="#FAA61A")
            self.show_timed_message("Mode", "Switched to FA (Zeus-X)")
            
        self.save_settings(self.mode_ev.get(), self.use_pfp.get(), self.disable_197.get(), self.mode_unclaimed.get(), self.mode_trial.get(), self.use_solver.get(), self.email_provider)

    def toggle_email_provider_click(self):
        providers = ["zeus", "lution"]
        current_idx = providers.index(self.email_provider) if self.email_provider in providers else -1
        self.email_provider = providers[(current_idx + 1) % len(providers)]
        self.btn_email_provider.config(text=f"MAIL: {self.email_provider.upper()}")
        self.current_manager.ACTIVE_PROVIDER = self.email_provider
        self.save_settings(self.mode_ev.get(), self.use_pfp.get(), self.disable_197.get(), self.mode_unclaimed.get(), self.mode_trial.get(), self.use_solver.get(), self.email_provider)

    def toggle_details_click(self):
        if self.details_visible:
            self.details_visible = False
            self.info_frame.pack_forget()
            self.btn_details.config(text="👁️ Show Details", bg="#5A5E66")
            self.root.geometry("280x190")
        else:
            self.details_visible = True
            self.info_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.btn_details.config(text="↰ Hide Details", bg="#7289DA")
            self.root.geometry("280x275")
    
    def toggle_solver_click(self):
        current = self.use_solver.get()
        self.use_solver.set(not current)
        
        if self.use_solver.get():
            self.btn_solver.config(text="SOLVER: ON", bg="#118AB2")
            self.show_timed_message("Config", "Solver Enabled.\nCaptchas will be extracted.")
        else:
            self.btn_solver.config(text="SOLVER: OFF", bg="#72767d")
            self.show_timed_message("Config", "Solver Disabled.\nBypassing captchas.")
            
        self.save_settings(self.mode_ev.get(), self.use_pfp.get(), self.disable_197.get(), self.mode_unclaimed.get(), self.mode_trial.get(), self.use_solver.get(), self.email_provider)
    
    def toggle_pfp_click(self):
        current = self.use_pfp.get()
        self.use_pfp.set(not current)
        
        if self.use_pfp.get():
            self.btn_pfp.config(text="PFP: ON", bg="#5865F2")
        else:
            self.btn_pfp.config(text="PFP: OFF", bg="#72767d")
            
        self.save_settings(self.mode_ev.get(), self.use_pfp.get(), self.disable_197.get(), self.mode_unclaimed.get(), self.mode_trial.get(), self.use_solver.get(), self.email_provider)
    
    def action_start(self):
        print(">> Start button clicked. Initiating Cycle...") 
        self.cycle_active[0] = False
        self.action_wipe_and_rotate(is_skip=True)

    def action_create_image(self):
        if self.mode_trial.get():
            mode_suffix = "trial"
        elif self.mode_unclaimed.get():
            mode_suffix = "unclaimed"
        else:
            mode_suffix = "standard"
            
        VIP_LOCK_PATH = os.path.join(SHARED_DIR, f"image_building_{mode_suffix}.lock")
        COOLDOWN_LOCK_PATH = os.path.join(SHARED_DIR, f"global_cooldown_{mode_suffix}.txt")
        
        if os.path.exists(VIP_LOCK_PATH):
            try:
                if time.time() - os.path.getmtime(VIP_LOCK_PATH) > 420: 
                    print(" [Bouncer] Stale VIP lock detected. Nuking it...")
                    os.remove(VIP_LOCK_PATH)
            except Exception:
                pass

        if os.path.exists(COOLDOWN_LOCK_PATH):
            try:
                with open(COOLDOWN_LOCK_PATH, "r") as f:
                    expiry = float(f.read().strip())
                if time.time() > expiry:
                    print(" [Bouncer] Expired cooldown lock detected. Nuking it...")
                    os.remove(COOLDOWN_LOCK_PATH)
            except Exception:
                pass

        if os.path.exists(COOLDOWN_LOCK_PATH):
            print(">> ⚠️ MANUAL ABORTED: A global cooldown is active!")
            return 
            
        if os.path.exists(VIP_LOCK_PATH):
            try:
                with open(VIP_LOCK_PATH, "r") as f:
                    locker_id = f.read().strip()
                
                if locker_id and locker_id != str(INSTANCE_ID):
                    print(f">> ⚠️ MANUAL ABORTED: Instance {locker_id} is building the cache!")
                    return
            except Exception:
                pass

        print(">> Image Creation Cycle Initiated. Nuking old cache...")
        self.image_cycle_active = True
        self.cycle_active[0] = False
        
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        
        if self.mode_trial.get():
            target_cache = os.path.join(SCRIPT_DIR, "golden_cache_trial")
        elif self.mode_unclaimed.get():
            target_cache = os.path.join(SCRIPT_DIR, "golden_cache_unclaimed")
        else:
            target_cache = os.path.join(SCRIPT_DIR, "golden_cache")
            
        if os.path.exists(target_cache):
            subprocess.run(["rm", "-rf", target_cache])
        
        self.action_wipe_and_rotate(is_skip=True)
    
    def add_info_row(self, label_text):
        frame = tk.Frame(self.info_frame, bg="#23272A")
        frame.pack(fill="x", pady=1)
        tk.Label(frame, text=label_text, bg="#23272A", fg="#99AAB5", width=12, anchor="w", font=("Arial", 9)).pack(side="left")
        lbl_value = tk.Entry(frame, bg="#2C2F33", fg="white", bd=0, font=("Consolas", 9), readonlybackground="#2C2F33")
        lbl_value.pack(side="left", fill="x", expand=True, padx=2)
        return lbl_value

    def show_timed_message(self, title, message):
        top = tk.Toplevel(self.root)
        top.title(title)
        top.geometry("300x120")
        top.attributes('-topmost', True)
        top.configure(bg="#2C2F33")
        x = self.root.winfo_x() + 20
        y = self.root.winfo_y() + 100
        top.geometry(f"+{x}+{y}")
        tk.Label(top, text=message, bg="#2C2F33", fg="white", font=("Arial", 10), wraplength=280).pack(expand=True, pady=10)
        self.root.after(2000, top.destroy)

    def run_clipboard_sync(self):
        last_text = ""
        while True:
            try:
                current_text = pyperclip.paste()
                if current_text and current_text != last_text:
                    last_text = current_text
                    p = subprocess.Popen(
                        ['xclip', '-selection', 'clipboard', '-display', MY_DISPLAY], 
                        stdin=subprocess.PIPE, 
                        stderr=subprocess.DEVNULL, 
                        stdout=subprocess.DEVNULL
                    )
                    p.communicate(input=current_text.encode('utf-8'))
            except: pass
            time.sleep(0.5)

    def hard_reset(self):
        self.image_cycle_active = False
        print(" [Reset] 💥 NUCLEAR RESET SEQUENCE...")

        if self.mode_trial.get() and getattr(self, 'current_trial_token', None):
            self.preserve_trial_token(self.current_email, self.current_pass, self.current_trial_token)

        try:
            if hasattr(self, 'current_pool_slot') and self.current_pool_slot is not None:
                print(f" [Reset] 🛡️ Destroying Container Slot {self.current_pool_slot}...")
                if router_manager.proxy_engine:
                    router_manager.proxy_engine.discard_proxy(self.current_pool_slot)
                self.current_pool_slot = None
            if router_manager.proxy_engine:
                router_manager.proxy_engine.disconnect()
        except Exception as e:
            print(f" [Reset] proxy Disconnect Warning: {e}")

        print(f" [Reset] 🛑 Nuking orphaned Docker containers for Instance {INSTANCE_ID}...")
        try:
            kill_cmd = f"docker ps -a -q --filter 'name=fuga_myst_inst{INSTANCE_ID}' | xargs -r docker rm -f"
            subprocess.run(kill_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass

        subprocess.run(["pkill", "-f", f"user-data-dir={MY_DATA_DIR}"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", f"Xephyr {MY_DISPLAY}"], stderr=subprocess.DEVNULL)
        
        time.sleep(0.2)

        print(" [Reset] 👋 Rebooting Fuga...")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def full_shutdown(self, *args):
        print("\n [Shutdown] 🛑 Executing Full System Cleanup before exiting...")

        if self.mode_trial.get() and getattr(self, 'current_trial_token', None):
            self.preserve_trial_token(self.current_email, self.current_pass, self.current_trial_token)

        try:
            if hasattr(self, 'current_pool_slot') and self.current_pool_slot is not None:
                if router_manager.proxy_engine:
                    router_manager.proxy_engine.discard_proxy(self.current_pool_slot)
                self.current_pool_slot = None
            if router_manager.proxy_engine:
                router_manager.proxy_engine.disconnect()
        except Exception:
            pass

        print(f" [Shutdown] 🛑 Nuking orphaned Docker containers for Instance {INSTANCE_ID}...")
        try:
            kill_cmd = f"docker ps -a -q --filter 'name=fuga_myst_inst{INSTANCE_ID}' | xargs -r docker rm -f"
            subprocess.run(kill_cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass

        subprocess.run(["pkill", "-f", f"user-data-dir={MY_DATA_DIR}"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", f"Xephyr {MY_DISPLAY}"], stderr=subprocess.DEVNULL)
        
        print(" [Shutdown] 👋 Exiting FUGA. All processes terminated.")
        
        os._exit(0)
    
    def startup_sequence(self):
        self.status_var.set("Initializing Brave...")
        try:
            if self.mode_trial.get():
                current_mode = "TRIAL"
            elif self.mode_unclaimed.get():
                current_mode = "UNCLAIMED"
            elif self.mode_ev.get():
                current_mode = "EV"
            else:
                current_mode = "FA"

            cleaner.perform_deep_clean(mode=current_mode)
            subprocess.run(["pkill", "-f", f"Xephyr {MY_DISPLAY}"], stderr=subprocess.DEVNULL)
            self.status_var.set("System Ready.")
        except Exception as e:
            messagebox.showerror("Error", f"Startup Failed: {e}")

    def start_dashboard_watchdog(self, active_flag, trial_token=None):
        if not active_flag[0]: return

        if self.mode_trial.get():
            self.status_var.set("⏳ Trial: Waiting for Extension Signal...")
        else:
            self.status_var.set("⏳ Captcha: Waiting for Extension Signal...")

        self.dashboard_success_handled = False

        timeout_ms = 240000 if self.mode_trial.get() else 70000

        def _timeout():
            if not active_flag[0] or getattr(self, 'dashboard_success_handled', False): return
            print("[Debug] ❌ Dashboard Timeout. Auto-saving and skipping...")
            self.status_var.set("❌ Timeout: Auto-Saving & Skipping...")
            
            self.action_save_email()
            
            self.action_skip_cycle()

        self.dashboard_timer = self.root.after(timeout_ms, _timeout)

    def execute_dashboard_success(self, active_flag, trial_token=None):
        if not active_flag[0] or getattr(self, 'dashboard_success_handled', False): return

        env_vm = os.environ.copy()
        env_vm["DISPLAY"] = MY_DISPLAY

        self.dashboard_success_handled = True
        if hasattr(self, 'dashboard_timer'):
            self.root.after_cancel(self.dashboard_timer)

        self.root.after(0, lambda: self.status_var.set("Signal Verified!"))
        self.root.after(0, lambda: self.btn_start.config(state="normal")) 
        
        if self.mode_unclaimed.get():
            time.sleep(random.uniform(1.0, 1.5))

        if self.mode_trial.get():
            self.root.after(0, lambda: self.status_var.set("✅ Tasks Done! Saving..."))
            
            if not os.path.exists("triggered.txt"):
                open("triggered.txt", 'a').close()
                
            try:
                with open("triggered.txt", "r+") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    existing = [line.strip() for line in f.readlines()]
                    line_to_add = f"{self.current_email} | {self.current_pass} | {trial_token}"
                    
                    if line_to_add not in existing:
                        f.seek(0, os.SEEK_END)
                        f.write(line_to_add + "\n")
                        print(" [Triggered] ✅ Account saved to triggered.txt")
                    else:
                        print(" [Triggered] ⚠️ Account already in triggered.txt. Skipping duplicate.")
                        
                    fcntl.flock(f, fcntl.LOCK_UN)
            except Exception as e: 
                print(f" [Error] Saving triggered: {e}")

        if self.mode_unclaimed.get() or self.mode_trial.get():
            if getattr(self, 'image_cycle_active', False):
                self.root.after(0, lambda: self.status_var.set("⏳ Loading Assets (15s)..."))
                
                def _unified_image_thread():
                    if not active_flag[0]: return
                    
                    time.sleep(5.0)
                    if not active_flag[0]: return
                    
                    self.root.after(0, lambda: self.status_var.set("🔄 Refreshing to load assets..."))
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+r"], env=env_vm)
                    
                    time.sleep(15.0) 
                    if not active_flag[0]: return
                    
                    if self.mode_unclaimed.get():
                        self.extract_token_ipc()
                    
                    self.root.after(0, lambda: self.status_var.set("📸 Building Cache..."))
                    time.sleep(2.0)
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+shift+w"], env=env_vm)
                    time.sleep(5.0)
                    
                    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
                    target_cache = "golden_cache_trial" if self.mode_trial.get() else "golden_cache_unclaimed"
                    golden_cache_path = os.path.join(SCRIPT_DIR, target_cache) 
                    source_cache = os.path.expanduser(f"~/.cache/BraveSoftware/Brave-Browser-{INSTANCE_ID}/Default/Cache/Cache_Data")
                    
                    subprocess.run(["cp", "-r", source_cache, golden_cache_path])
                    subprocess.run(["find", golden_cache_path, "-type", "f", "-exec", "touch", "-d", "15 minutes ago", "{}", "+"])
                    
                    print(f" [Image] ✅ {target_cache} creation complete!")

                    self.root.after(0, lambda: self.action_wipe_and_rotate(is_skip=True, is_image_cycle_end=True))
                    
                threading.Thread(target=_unified_image_thread, daemon=True).start()
            else:
                self.root.after(0, lambda: self.status_var.set("✅ Auto-Pilot: Extracting..."))
                
                def _unified_auto_save():
                    if not active_flag[0]: return
                    time.sleep(0.5) 
                    
                    
                    is_skip_extraction = True if self.mode_trial.get() else False
                    self.root.after(0, lambda: self.action_wipe_and_rotate(is_skip=is_skip_extraction))

                threading.Thread(target=_unified_auto_save, daemon=True).start()
        else:
            if getattr(self, 'image_cycle_active', False):
                self.root.after(0, lambda: self.status_var.set("⏳ Image Cycle: Waiting to refresh..."))
                
                def _normal_refresh_thread():
                    if not active_flag[0]: return
                    
                    time.sleep(5.0)
                    if not active_flag[0]: return
                    
                    self.root.after(0, lambda: self.status_var.set("🔄 Refreshing page (Image Cycle)..."))
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+r"], env=env_vm)
                    
                    time.sleep(15.0) 
                    if not active_flag[0]: return
                    
                    self.root.after(0, lambda: self.action_check_inbox(active_flag))
                    
                threading.Thread(target=_normal_refresh_thread, daemon=True).start()
                
            else: 
                self.root.after(0, lambda: self.action_check_inbox(active_flag))
    
    def get_fast_public_ip(self):
        try:
            cmd = ["dig", "@208.67.222.222", "myip.opendns.com", "+short"]
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=1).decode('utf-8').strip()
            if result and len(result) > 6:
                return result
        except: 
            pass
        return None

    def action_save_email(self):
        if self.mode_trial.get():
            if getattr(self, 'current_trial_token', None):
                self.preserve_trial_token(self.current_email, self.current_pass, self.current_trial_token)
                self.btn_save_email.config(text="✅ SAVED!", bg="#2D7D46")
                self.root.after(2000, lambda: self.btn_save_email.config(text="💾 Save", bg="#1971c2"))
            else:
                self.status_var.set("Trial Mode: No token to save")
            return

        self.btn_save_email.config(state="disabled", text="⏳ SAVING...")

        try:
            if self.mode_ev.get():
                save_file = f"saved_emails_EV_{INSTANCE_ID}.json"
            else:
                save_file = f"saved_emails_FA_{INSTANCE_ID}.json"

            if not hasattr(self, 'current_account_dict') or not self.current_account_dict:
                self.show_timed_message("Error", "No account data in memory!")
                self.btn_save_email.config(state="normal", text="💾 SAVE EMAIL")
                return

            current_account_data = {
                "Email": self.current_email,
                "Password": self.current_pass,
                "full_string": self.current_full_string,
                "RefreshToken": self.current_account_dict.get("refresh_token"),
                "ClientId": self.current_account_dict.get("client_id")
            }

            database = []
            if os.path.exists(save_file):
                try:
                    with open(save_file, "r") as f:
                        content = f.read().strip()
                        if content: database = json.loads(content)
                except: database = []
            
            if not isinstance(database, list): database = []

            email_to_save = current_account_data.get("Email", "")
            if any(acc.get("Email") == email_to_save for acc in database):
                self.btn_save_email.config(text="⚠️ ALREADY SAVED", bg="#F57C00")
                return

            database.append(current_account_data)
            
            with open(save_file, "w") as f:
                json.dump(database, f, indent=4)
                
            self.btn_save_email.config(text="✅ SAVED!", bg="#2D7D46")
            print(f" [Save] Saved to {save_file}")
            
        except Exception as e:
            print(f"Save Error: {e}")
            self.show_timed_message("Error", f"Could not save: {e}")
            self.btn_save_email.config(state="normal", text="💾 SAVE EMAIL")
    
    def action_skip_cycle(self):
        try:
            self.btn_skip.config(state="disabled")
            self.btn_check_mail.config(state="disabled")
            self.btn_start.config(state="disabled")
        except: pass

        def _thread():
            self.cycle_active[0] = False
            self.status_var.set("⏭️ Skipping... Nuking Slot...")
            print(" [Skip] ⏭️ Skip requested. Aborting current cycle...")
            
            subprocess.run(["pkill", "-f", f"user-data-dir={MY_DATA_DIR}"], stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-f", f"Xephyr {MY_DISPLAY}"], stderr=subprocess.DEVNULL)
            
            if hasattr(self, 'current_pool_slot') and self.current_pool_slot is not None:
                print(f" [Skip] 🗑️ Force-discarding Slot {self.current_pool_slot}...")
                if router_manager.proxy_engine:
                    router_manager.proxy_engine.discard_proxy(self.current_pool_slot)
                self.current_pool_slot = None
            
            self.current_email = None; self.current_pass = None; self.current_user = None; self.current_disp = None
            self.root.after(0, self._clear_ui_entries)
            
            if self.mode_trial.get():
                current_mode = "TRIAL"
            elif self.mode_unclaimed.get():
                current_mode = "UNCLAIMED"
            elif self.mode_ev.get():
                current_mode = "EV"
            else:
                current_mode = "FA"

            cleaner.perform_deep_clean(mode=current_mode)
            
            self.root.after(0, lambda: self.action_wipe_and_rotate(is_skip=True))
            
            self.root.after(2000, lambda: self.btn_skip.config(state="normal"))

        threading.Thread(target=_thread, daemon=True).start()
    
    def action_wipe_and_rotate(self, is_skip=False, is_image_cycle_end=False):
        self.btn_check_mail.config(text="📩 CHECK INBOX", bg="#7289DA", state="disabled")
        
        self.cycle_active = [True]
        current_flag = self.cycle_active

        def _thread():

            nonlocal is_image_cycle_end

            if not is_skip:
                self.extract_token_ipc()

            self.status_var.set("Closing Brave...")
            subprocess.run(["pkill", "-f", f"user-data-dir={MY_DATA_DIR}"], stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-f", f"Xephyr {MY_DISPLAY}"], stderr=subprocess.DEVNULL)
            
            if self.mode_trial.get():
                mode_suffix = "trial"
            elif self.mode_unclaimed.get():
                mode_suffix = "unclaimed"
            else:
                mode_suffix = "standard"

            VIP_LOCK_PATH = os.path.join(SHARED_DIR, f"image_building_{mode_suffix}.lock")
            COOLDOWN_LOCK_PATH = os.path.join(SHARED_DIR, f"global_cooldown_{mode_suffix}.txt")

            while True:
                was_delayed_by_lock = False

                MAX_LOCK_AGE = 420
                
                while os.path.exists(VIP_LOCK_PATH):
                    if not current_flag[0]: return
                    was_delayed_by_lock = True
                    
                    try:
                        lock_age = time.time() - os.path.getmtime(VIP_LOCK_PATH)
                        if lock_age > MAX_LOCK_AGE:
                            print(f" [VIP Lock] Stale lock detected ({lock_age:.0f}s old). Instance crashed! Nuking lock...")
                            try:
                                os.remove(VIP_LOCK_PATH)
                            except FileNotFoundError:
                                pass
                            break
                    except Exception:
                        pass
                    
                    try:
                        with open(VIP_LOCK_PATH, "r") as f:
                            allowed_instance = f.read().strip()
                    except Exception:
                        allowed_instance = None
                    
                    if allowed_instance == str(INSTANCE_ID):
                        break
                    else:
                        self.status_var.set(f"⏳ Waiting for Instance {allowed_instance} to build cache...")
                        time.sleep(2)

                if os.path.exists(COOLDOWN_LOCK_PATH):
                    try:
                        with open(COOLDOWN_LOCK_PATH, "r") as f:
                            expiry = float(f.read().strip())
                        
                        while time.time() < expiry:
                            if not current_flag[0]: return
                            was_delayed_by_lock = True
                            
                            remaining = int(expiry - time.time())
                            mins, secs = divmod(remaining, 60)
                            self.status_var.set(f"⏳ Cooldown: {mins}:{secs:02d} left")
                            time.sleep(1)
                            
                        if os.path.exists(COOLDOWN_LOCK_PATH):
                            os.remove(COOLDOWN_LOCK_PATH)
                    except Exception:
                        pass

                try:
                    usage_kb = 0
                    if getattr(router_manager, 'proxy_engine', None) is not None:
                        usage_kb = router_manager.proxy_engine.get_last_session_data_usage()
                        
                    if is_image_cycle_end:
                        print(f" [DataTracker] Image cycle complete. Setting 4-min cooldown.")
                        self.image_cycle_active = False 
                        
                        with open(COOLDOWN_LOCK_PATH, "w") as f:
                            f.write(str(time.time() + 180))
                            
                        if os.path.exists(VIP_LOCK_PATH):
                            os.remove(VIP_LOCK_PATH)
                            
                        is_image_cycle_end = False 
                        continue 
                            
                    elif getattr(self, 'image_cycle_active', False):
                        if not os.path.exists(VIP_LOCK_PATH):
                            print(" [DataTracker] Image Cycle detected! Securing VIP Lock...")
                            try:
                                with open(VIP_LOCK_PATH, "x") as f:
                                    f.write(str(INSTANCE_ID))
                            except FileExistsError:
                                print(" [DataTracker] Lost the millisecond race! Restarting lock check...")
                                time.sleep(0.5)
                                continue
                        else:
                            print(f" [DataTracker] Image cycle passing through safely. Loop bypassed.")
                            
                            try:
                                os.utime(VIP_LOCK_PATH, None)
                            except Exception:
                                pass
                            
                    elif usage_kb > 2500:
                        if was_delayed_by_lock:
                            print(f" [DataTracker] High usage ({usage_kb:.2f} KB), but we just waited for a global sync. Skipping to clear old data.")
                            
                        else:
                            print(f" [DataTracker] 📸 High usage ({usage_kb:.2f} KB). Locking out other instances...")
                            try:
                                with open(VIP_LOCK_PATH, "x") as f:
                                    f.write(str(INSTANCE_ID))
                                    
                                self.root.after(0, self.action_create_image)
                                return 
                            except FileExistsError:
                                print(" [DataTracker] Tried to set lock, but another instance beat us by milliseconds!")
                                time.sleep(0.5)
                                continue
                                    
                except Exception as e:
                    print(f"⚠️ Could not check data usage/locks: {e}")
                    
                break 
            
            self.current_email = None; self.current_pass = None; self.current_user = None; self.current_disp = None
            self.root.after(0, self._clear_ui_entries)
            
            self.status_var.set("Cleaning System...")
            if self.mode_trial.get():
                current_mode = "TRIAL"
            elif self.mode_unclaimed.get():
                current_mode = "UNCLAIMED"
            elif self.mode_ev.get():
                current_mode = "EV"
            else:
                current_mode = "FA"

            cleaner.perform_deep_clean(mode=current_mode)
            
            subprocess.run(["pkill", "-f", f"Xephyr {MY_DISPLAY}"], stderr=subprocess.DEVNULL)

            while self.use_solver.get():
                self.status_var.set("Checking for online workers...")
                
                if solver.is_ready():
                    break
                
                self.status_var.set("Paused: Waiting for online worker...")
                print("Waiting for online worker...")
                
                for _ in range(10):
                    if not self.use_solver.get():
                        break
                    if not current_flag[0]:
                        return
                    time.sleep(1)
            
            self.status_var.set("Rotating IP...")
            
            if getattr(router_manager, 'proxy_engine', None) is None:
                print(f" [Setup] Starting DataImpulse Proxy Engine...")
                router_manager.proxy_engine = router_manager.DataImpulseManager()
            
            if router_manager.rotate_ip_guaranteed(force_proxy=self.disable_197.get()):
                if router_manager.proxy_engine.is_active():
                    self.status_var.set("🛡️ proxt Active! Launching...")
                else:
                    self.status_var.set("⚡ Hardware IP! Launching...")
                
                try:
                        base_dir = MY_DATA_DIR
                        profile_dir = os.path.join(base_dir, "Default")
                        
                        os.makedirs(base_dir, exist_ok=True)
                        os.makedirs(profile_dir, exist_ok=True)

                        local_state_data = {
                            "brave": {
                                "p3a": {
                                    "enabled": False,
                                    "notice_acknowledged": True
                                },
                                "rewards": {
                                    "ac_enabled": False,
                                    "enabled": False
                                }
                            },
                            "browser": {
                                "enabled_labs_experiments": [],
                                "last_redirect_origin": ""
                            }
                        }

                        if router_manager.proxy_engine.is_active():
                            accept_langs = "en-US,en"
                        else:
                            accept_langs = "ar-EG,ar"

                        prefs_data = {
                            "brave": {
                                "p3a": {"enabled": False},
                                "brian": {"show_onboarding": False},
                                "wallet": {"show_backup_phrase": False}
                            },
                            "browser": {
                                "has_seen_welcome_page": True,
                                "check_default_browser": False
                            },
                            "intl": {
                                "accept_languages": accept_langs,
                                "selected_languages": accept_langs
                            }
                        }

                        with open(os.path.join(base_dir, "Local State"), "w") as f:
                            json.dump(local_state_data, f)
                            
                        with open(os.path.join(profile_dir, "Preferences"), "w") as f:
                            json.dump(prefs_data, f)

                except Exception as e:
                        print(f"State Injection Error: {e}")

                
                current_trial_token = None
                if self.mode_trial.get():
                    raw_data = self.pop_trial_token()
                    if not raw_data:
                        self.status_var.set("❌ Out of Tokens to Trigger!")
                        self.root.after(0, lambda: self.btn_start.config(state="normal"))
                        return
                    
                    parts = [p.strip() for p in raw_data.split("|")]
                    if len(parts) >= 3:
                        self.current_email = parts[0]
                        self.current_pass = parts[1]
                        current_trial_token = parts[2]
                        self.current_trial_token = current_trial_token
                        self.root.after(0, lambda: self.lbl_email.config(state="normal") or self.lbl_email.insert(0, self.current_email) or self.lbl_email.config(state="readonly"))
                        self.root.after(0, lambda: self.lbl_pass.config(state="normal") or self.lbl_pass.insert(0, self.current_pass) or self.lbl_pass.config(state="readonly"))
                        self.root.after(0, lambda: self.btn_save_email.config(state="normal", text="💾 Save", bg="#1971c2"))
                    else:
                        current_trial_token = parts[0]
                        self.current_trial_token = current_trial_token
                        self.root.after(0, lambda: self.btn_save_email.config(state="normal", text="💾 Save", bg="#1971c2"))

                unique_pfp_payload = None
                if self.use_pfp.get():
                    print(" [Setup] Generating unique Identicon...")
                    unique_pfp_payload = generate_identicon_bmp()
                else:
                    print(" [Setup] PFP Disabled. Skipping generation.")

                ext_path, gpu_name = self.ext_gen.create_extension(
                    avatar_payload=unique_pfp_payload, 
                    is_unclaimed=self.mode_unclaimed.get(),
                    trial_token=current_trial_token,
                    use_solver=self.use_solver.get()
                )

                full_ext_arg = f"--load-extension={ext_path}"

                
                scr_w, scr_h = random.choice([ (1680, 1050), (1368, 768), (1440, 900), (1920, 1080), (1600, 900), (1536, 864)])
                if random.random() < 0.3:
                    win_w, win_h = scr_w, scr_h; pos_x, pos_y = 0, 0
                else:
                    gap_w = random.randint(30, 150); gap_h = random.randint(40, 80)
                    win_w = scr_w - gap_w; win_h = scr_h - gap_h
                    pos_x = random.randint(0, gap_w); pos_y = random.randint(0, gap_h)

                
                display_num = MY_DISPLAY.replace(":", "")
                subprocess.run(["rm", "-f", f"/tmp/.X{display_num}-lock", f"/tmp/.X11-unix/X{display_num}"], stderr=subprocess.DEVNULL)
                
                subprocess.Popen(["Xephyr", MY_DISPLAY, "-ac", "-screen", f"{scr_w}x{scr_h}", "-title", f"Xephyr Instance {INSTANCE_ID}"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                time.sleep(0.1)
                
                env_vm = os.environ.copy()
                env_vm["DISPLAY"] = MY_DISPLAY
                
                env_vm["GTK_USE_PORTAL"] = "0"
                if "XDG_CURRENT_DESKTOP" in env_vm:
                    del env_vm["XDG_CURRENT_DESKTOP"]
                    
                if "DBUS_SESSION_BUS_ADDRESS" in env_vm:
                    del env_vm["DBUS_SESSION_BUS_ADDRESS"]
                
                if hasattr(self, 'current_pool_slot') and self.current_pool_slot is not None:
                    router_manager.proxy_engine.discard_proxy(self.current_pool_slot)
                    self.current_pool_slot = None

                active_proxy_port = None
                if router_manager.proxy_engine.is_active() or self.disable_197.get():
                    print(" [LAUNCH] 🛡️ proxy Mode: Pulling Proactive Container...")
                    active_proxy_port, slot_id = router_manager.proxy_engine.get_ready_proxy()
                    self.current_pool_slot = slot_id

                subprocess.Popen(["openbox"], env=env_vm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                benign_features = [
                    "DocumentPictureInPictureAPI",
                    "EyeDropperAPI",
                    "ComputePressure",
                    "BarcodeDetector",
                    "DigitalGoodsAPI"
                ]
                
                features_to_disable = random.sample(benign_features, random.randint(1, 3))
                
                base_disabled_features = [
                    "BraveShields", "CrashReporting", "WebDiscoveryProject", 
                    "BraveRewards", "BraveWallet", "BraveNews", "BraveSync", 
                    "BraveLeo", "BraveAIChat", "OptimizationGuideModelDownloading", 
                    "Braveproxy", "BraveP3A", "BraveStatsPing", "SafeBrowsing", "Variations"
                ]
                
                final_disabled_string = ",".join(base_disabled_features + features_to_disable)
                

                cmd = [
                    "brave-browser",
                    
                    "--disable-gpu-composition", 
                    "--disable-smooth-scrolling", 
                    "--wm-window-animations-disabled",
                    "--disable-dev-shm-usage", 
                    "--disable-quic",
                    "--dns-result-order=ipv4first",
                    "--disable-component-update",

                    "--no-first-run",
                    "--disable-fre",
                    f"--user-data-dir={MY_DATA_DIR}",
                    "--no-default-browser-check",
                    f"--window-size={win_w},{win_h}",
                    f"--window-position={pos_x},{pos_y}", 
                    full_ext_arg, 
                    
                    "--disable-infobars",
                    "--disable-notifications",
                    "--disable-popup-blocking",
                    
                    "--disable-breakpad",
                    "--disable-crash-reporter",
                    "--disable-logging",
                    "--log-level=3",
                    "--no-service-autorun",
                    "--password-store=basic",
                    "--ignore-gpu-blocklist", 
                    "--enable-webgl", 
                    "--enable-webgl2",
                    f"--disable-features={final_disabled_string}",
                    "--disable-sync"
                ]

                if active_proxy_port:
                    cmd.append(f"--proxy-server=http://127.0.0.1:{active_proxy_port}")
                else:
                    print(" [LAUNCH] ⚡Direct Connection.")
                    cmd.append("--no-proxy-server")

                if self.mode_trial.get():
                    cmd.append("https://discord.com/quest-home")
                elif self.mode_unclaimed.get():
                    invite_urls = [
                        "https://discord.com/invite/minecraft",
                        "https://discord.com/invite/pubgm-mena",
                    ]
                    chosen_url = random.choice(invite_urls)
                    cmd.append(chosen_url)
                else:
                    cmd.append("https://discord.com/register")
                
                subprocess.Popen(cmd, env=env_vm, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                self.status_var.set(f"Spoofed: {gpu_name[:15]}...")
                
                try: 
                    self.btn_start.config(state="disabled") 
                except: pass
                
                if self.mode_trial.get():
                    self.root.after(0, lambda: self.start_dashboard_watchdog(current_flag, current_trial_token))
                else:
                    self.root.after(0, lambda: self.start_login_watchdog(current_flag))
            
            else:
                self.status_var.set("proxy Failed (No Success Msg).")
                self.root.after(0, lambda: messagebox.showerror("Error", "Connection Failed!)"))
            
        threading.Thread(target=_thread, daemon=True).start()

    def _clear_ui_entries(self):
        self.current_trial_token = None
        try: self.btn_save_email.config(state="disabled", text="💾 Save", bg="#1971c2")
        except: pass
        for entry in [self.lbl_email, self.lbl_display, self.lbl_user, self.lbl_pass]:
            entry.config(state="normal"); entry.delete(0, tk.END); entry.config(state="readonly")

    def start_login_watchdog(self, active_flag):
        if not active_flag[0]: return
        self.status_var.set("⏳ Waiting for Form via IPC...")
        self.login_success_handled = False

        def _timeout():
            if not active_flag[0] or getattr(self, 'login_success_handled', False): return
            self.status_var.set("❌ Timeout: Retrying Cycle...")
            print("[Debug] Timeout. Form not found. Triggering Auto-Restart...")
            self.action_start()

        timeout_ms = 45000 if getattr(self, 'image_cycle_active', False) else 20000
        self.login_timer = self.root.after(timeout_ms, _timeout)

    def execute_login_success(self, active_flag):
        if not active_flag[0] or getattr(self, 'login_success_handled', False): return
        
        self.login_success_handled = True
        if hasattr(self, 'login_timer'):
            self.root.after_cancel(self.login_timer)

        self.root.after(0, lambda: self.status_var.set("✅ Signal Detected! Purchasing..."))
        self.root.after(0, lambda: self.action_generate_identity(active_flag))
    
    def action_generate_identity(self, active_flag):
        if self.mode_trial.get():
            self.status_var.set("Trial Mode: Skipping Identity Gen")
            return

        mode_str = "UNCLAIMED" if self.mode_unclaimed.get() else ('EV' if self.mode_ev.get() else 'FA')
        self.status_var.set(f"Purchasing ({mode_str})...")
        try: self.btn_start.config(state="disabled") 
        except: pass

        def _thread():
            if not active_flag[0]: return
            
            if self.mode_unclaimed.get():
                mail_data = {
                    "email": "", 
                    "password": "", 
                    "full_string": "", 
                    "valid": True,
                    "refresh_token": None,
                    "client_id": None
                }
            else:
                mail_mode = "EV" if self.mode_ev.get() else "FA"
                
                mail_data = self.current_manager.buy_account(mode=mail_mode)
                
                if not mail_data.get("valid"):
                    self.root.after(0, lambda: self.status_var.set("Purchase Failed."))
                    self.root.after(0, lambda: self.btn_start.config(state="normal"))
                    self.root.after(0, lambda: self.hard_reset()) 
                    return
            
            is_proxy_active = router_manager.proxy_engine.is_active()
            persona = identity.generate_identity(use_western_names=is_proxy_active)
            
            self.root.after(0, lambda: self.update_ui_identity(persona, mail_data, active_flag))
        threading.Thread(target=_thread, daemon=True).start()

    def update_ui_identity(self, persona, mail_data, active_flag):
        self.current_email = mail_data.get('email', '')
        self.current_pass = mail_data.get('password', '')
        self.current_user = persona['username']
        self.current_disp = persona['display_name']
        self.current_full_string = mail_data.get('full_string', '')
        
        self.current_account_dict = mail_data
        
        for entry in [self.lbl_email, self.lbl_display, self.lbl_user, self.lbl_pass]:
            entry.config(state="normal"); entry.delete(0, tk.END)
        
        self.lbl_email.insert(0, str(self.current_email or ''))
        self.lbl_display.insert(0, str(self.current_disp or ''))
        self.lbl_user.insert(0, str(self.current_user or ''))
        self.lbl_pass.insert(0, str(self.current_pass or ''))

        for entry in [self.lbl_email, self.lbl_display, self.lbl_user, self.lbl_pass]:
            entry.config(state="readonly")

        try:
            self.btn_save_email.config(state="normal", text="💾 SAVE EMAIL", bg="#1971c2")
        except: pass
        
        self.btn_check_mail.config(state="normal", text="📩 CHECK INBOX", bg="#7289DA")
        self.root.after(0, lambda: self.run_auto_filler(active_flag))

    def run_auto_filler(self, active_flag):
        if self.mode_trial.get():
            self.status_var.set("Trial Mode: Skipping Auto-Fill")
            return

        def _fill_sequence():
            if not active_flag[0]: return
            self.status_var.set("🤖 Humanized Auto-Fill...")
            
            time.sleep(random.uniform(0.05, 0.15)) 

            env_vm = os.environ.copy()
            env_vm["DISPLAY"] = MY_DISPLAY

            def send_keys(keys, speed="normal"):
                if speed == "fast":
                    typing_delay = str(random.randint(10, 20))
                elif speed == "medium":
                    typing_delay = str(random.randint(20, 40))
                else:
                    typing_delay = str(random.randint(40, 80))
                subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", typing_delay, keys], env=env_vm)
            
            def press(key):
                subprocess.run(["xdotool", "key", "--clearmodifiers", key], env=env_vm)

            def human_type(target_text, speed="medium"): 
                if random.random() < 0.35 and len(target_text) > 3:
                    mistake_idx = random.randint(1, len(target_text) - 1)
                    send_keys(target_text[:mistake_idx], speed=speed)
                    
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    send_keys(wrong_char, speed=speed)
                    
                    time.sleep(random.uniform(0.08, 0.12))
                    press("BackSpace")
                    time.sleep(random.uniform(0.05, 0.08))
                    
                    send_keys(target_text[mistake_idx:], speed=speed)
                else:
                    send_keys(target_text, speed=speed)

            try:
                rand_x = str(random.randint(300, 400))
                rand_y = str(random.randint(300, 400))
                
                subprocess.run([
                    "xdotool", "search", "--onlyvisible", "--class", "brave-browser", 
                    "windowfocus",       
                    "windowraise",       
                    "mousemove", "--window", "%1", rand_x, rand_y, 
                    "click", "1"
                ], env=env_vm)

                time.sleep(random.uniform(0.05, 0.11))
                
                press("ctrl+l"); time.sleep(0.05)
                press("Escape"); time.sleep(0.05)
                
                press("Tab"); time.sleep(0.05)

                if self.mode_unclaimed.get():
                    human_type(self.current_disp, speed="fast")
                else:
                    human_type(self.current_email, speed="fast")
                    time.sleep(random.uniform(0.1, 0.15)); press("Tab"); human_type(self.current_disp, speed="fast")
                    time.sleep(random.uniform(0.1, 0.15));  press("Tab"); human_type(self.current_user, speed="fast")
                    time.sleep(random.uniform(0.1, 0.15));  press("Tab"); human_type(self.current_pass, speed="fast")
                

                self.status_var.set("⏳ Waiting for DOB fields...")
                
                time.sleep(random.uniform(0.1, 0.15))

                def process_dob_field(field_name, coords_attr, scroll_calls):
                    wait_time = 0
                    while not getattr(self, coords_attr, None) and wait_time < 50:
                        time.sleep(0.1)
                        wait_time += 1
                    
                    btn_coords = getattr(self, coords_attr, None)
                    if not btn_coords:
                        print(f"[-] Auto-Filler timed out waiting for {field_name} button.")
                        return

                    self.status_var.set(f"🤖 Clicking {field_name}...")
                    
                    action_handler(env_vm, btn_coords, action_type="move", abort_check=lambda: not self.cycle_active[0], speed="fast")
                    time.sleep(random.uniform(0.02, 0.05))
                    action_handler(env_vm, btn_coords, action_type="click", abort_check=lambda: not self.cycle_active[0], speed="fast")
                    
                    self.active_dropdown_coords = None
                    wait_time = 0
                    while not getattr(self, 'active_dropdown_coords', None) and wait_time < 30:
                        time.sleep(0.1)
                        wait_time += 1
                        
                    dd_coords = getattr(self, 'active_dropdown_coords', None)
                    if not dd_coords:
                        print(f"[-] Auto-Filler timed out waiting for {field_name} dropdown menu.")
                        return
                        
                    self.status_var.set(f"🤖 Scrolling {field_name}...")
                    
                    action_handler(env_vm, dd_coords, action_type="move", abort_check=lambda: not self.cycle_active[0], speed="fast")
                    time.sleep(random.uniform(0.02, 0.05))
                    
                    for _ in range(scroll_calls):
                        action_handler(env_vm, dd_coords, action_type="scroll", abort_check=lambda: not self.cycle_active[0], speed="fast")
                        time.sleep(random.uniform(0.05, 0.1))
                    
                    action_handler(env_vm, dd_coords, action_type="click", abort_check=lambda: not self.cycle_active[0], speed="fast")
                    
                    self.active_dropdown_coords = None
                    time.sleep(random.uniform(0.1, 0.2))

                process_dob_field("Month", "dob_month_coords", scroll_calls=random.randint(0, 1))
                
                process_dob_field("Day", "dob_day_coords", scroll_calls=random.randint(0, 2))
                
                process_dob_field("Year", "dob_year_coords", scroll_calls=random.randint(2, 3))
                
                
                audit_passed = False
                
                while not audit_passed and self.cycle_active[0]:
                
                    
                    self.status_var.set("⏳ Waiting for TOS Checkbox...")
                    
                    wait_time = 0
                    while not getattr(self, 'latest_tos_coords', None) and wait_time < 20:
                        time.sleep(random.uniform(0.05, 0.1)) 
                        wait_time += 1
                    
                    if getattr(self, 'latest_tos_coords', None):
                        box_coords = self.latest_tos_coords
                        
                        self.status_var.set("🤖 Hovering TOS...")
                        action_handler(env_vm, box_coords, action_type="move", abort_check=lambda: not self.cycle_active[0], speed="fast")
                        
                        time.sleep(random.uniform(0.02, 0.05))
                        
                        self.status_var.set("🤖 Clicking TOS...")
                        action_handler(env_vm, box_coords, action_type="click", abort_check=lambda: not self.cycle_active[0], speed="fast")
                        
                        self.latest_tos_coords = None
                        time.sleep(random.uniform(0.05, 0.1)) 
                    else:
                        print("[-] Auto-Filler timed out waiting for TOS coordinates.")


                    self.status_var.set("⏳ Checking Create Button...")
                    
                    if getattr(self, 'create_needs_scroll', False):
                        self.status_var.set("🤖 Scrolling to reveal button...")
                        
                        action_handler(env_vm, None, action_type="scroll", abort_check=lambda: not self.cycle_active[0], speed="fast")
                        
                        self.create_needs_scroll = False
                        time.sleep(0.05) 
                    
                    self.status_var.set("⏳ Waiting for Create Button...")
                    
                    wait_time = 0
                    while not getattr(self, 'latest_create_coords', None) and wait_time < 50:
                        time.sleep(0.1)
                        wait_time += 1
                    
                    if getattr(self, 'latest_create_coords', None):
                        box_coords = self.latest_create_coords
                        
                        self.status_var.set("🤖 Hovering Create Account...")
                        action_handler(env_vm, box_coords, action_type="move", abort_check=lambda: not self.cycle_active[0], speed="fast")
                        time.sleep(random.uniform(0.02, 0.05))
                        
                        self.status_var.set("🤖 Clicking Create Account...")
                        action_handler(env_vm, box_coords, action_type="click", abort_check=lambda: not self.cycle_active[0], speed="fast")
                        
                        self.latest_create_coords = None
                    else:
                        print("[-] Auto-Filler timed out waiting for Create Button coordinates.")

                    self.status_var.set("⏳ Awaiting JS Form Audit...")
                    self.latest_audit_result = None
                    wait_time = 0
                    
                    while not self.latest_audit_result and wait_time < 60: 
                        if not self.cycle_active[0]: return
                        time.sleep(0.1)
                        wait_time += 1
                        
                    if self.latest_audit_result == "PASS":
                        audit_passed = True
                    elif isinstance(self.latest_audit_result, dict):
                        missed = self.latest_audit_result
                        self.status_var.set("⚠️ Repairing missed fields...")
                        
                        if missed.get("month"): process_dob_field("Month", "dob_month_coords", scroll_calls=random.randint(0, 1))
                        if missed.get("day"): process_dob_field("Day", "dob_day_coords", scroll_calls=random.randint(0, 2))
                        if missed.get("year"): process_dob_field("Year", "dob_year_coords", scroll_calls=random.randint(2, 3))
                        
                    else:
                        print("[-] Timed out waiting for JS audit signal. Assuming success.")
                        audit_passed = True

                if self.cycle_active[0]:
                    self.status_var.set("✅ Form Passed! Auto-Solving Captcha...")
                    self.lbl_status.config(fg="#3BA55C")
                    
                    self.root.after(0, lambda: self.start_dashboard_watchdog(active_flag))

            except Exception as e:
                print(f"Auto-Fill Error: {e}")
                self.status_var.set("Auto-Fill Error.")

        threading.Thread(target=_fill_sequence, daemon=True).start()
    
    def action_check_inbox(self, active_flag=None):
        if self.mode_trial.get():
            self.status_var.set("Trial Mode: No Inbox")
            return
            
        if not self.current_full_string: return
        current_flag = active_flag if active_flag else self.cycle_active
        
        def _thread():
            max_retries = 2
            link = None
            
            for attempt in range(1, max_retries + 1):
                if not current_flag[0]: return
                if not self.current_full_string: 
                    return

                status_msg = f"Checking Inbox ({attempt}/{max_retries})..."
                btn_msg = f"Checking ({attempt})..."
                
                self.root.after(0, lambda m=status_msg: self.status_var.set(m))
                self.root.after(0, lambda t=btn_msg: self.btn_check_mail.config(state="disabled", text=t))
                
                print(f" [Inbox] Starting Attempt {attempt} of {max_retries}...")
                
                check_mode = "EV" if self.mode_ev.get() else "FA"

                link = self.current_manager.get_verification_link(self.current_account_dict, mode=check_mode)
                
                if link:
                    print(f" [Inbox] ✅ Success on attempt {attempt}!")
                    break
                
                print(f" [Inbox] Attempt {attempt} returned no link. Retrying...")
            
            if link:
                self.root.after(0, lambda: self.process_verification_loop(link, current_flag))
            else:
                print(" [Inbox] ❌ Link not found (Max Retries). Auto-skipping...")
                self.root.after(0, lambda: self.status_var.set("Link Timeout: Auto-Skipping..."))
                self.root.after(0, lambda: self.action_wipe_and_rotate(is_skip=True))

        threading.Thread(target=_thread, daemon=True).start()

    def process_verification_loop(self, link, active_flag):
        self.status_var.set("Link Found! Instant Pasting...")
        self.btn_check_mail.config(text="⚡ CLEAN PASTE...", bg="#3BA55C")
        
        def _paste_sequence():
            if not active_flag[0]: return
            with self.window_lock:
                env_vm = os.environ.copy()
                env_vm["DISPLAY"] = MY_DISPLAY
                
                try:
                    clean_link = link.strip()
                    p = subprocess.Popen(
                        ['xclip', '-selection', 'clipboard', '-display', MY_DISPLAY], 
                        stdin=subprocess.PIPE
                    )
                    p.communicate(input=clean_link.encode('utf-8'))
                
                    wid = subprocess.check_output(["xdotool", "search", "--onlyvisible", "--class", "brave-browser"], env=env_vm).decode().strip().split('\n')[-1]
                    geom = subprocess.check_output(["xdotool", "getwindowgeometry", "--shell", wid], env=env_vm).decode()
                    width = int([line.split('=')[1] for line in geom.split('\n') if "WIDTH" in line][0])
                    height = int([line.split('=')[1] for line in geom.split('\n') if "HEIGHT" in line][0]) 
                    
                    subprocess.run(["xdotool", "mousemove", "--window", wid, str(width // 2), "60", "click", "1"], env=env_vm)
                    time.sleep(0.03)
                    
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "BackSpace"], env=env_vm) 
                    time.sleep(0.03)
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"], env=env_vm)
                    time.sleep(0.03)
                    subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"], env=env_vm)
                    
                    self.root.after(0, lambda: self.btn_start.config(state="normal"))

                    self.root.after(0, lambda: self.start_verification_watchdog(active_flag))

                except Exception as e:
                    print(f"Injection Error: {e}")

        threading.Thread(target=_paste_sequence, daemon=True).start()

    def start_verification_watchdog(self, active_flag):
        if not active_flag[0]: return
        self.status_var.set("⏳ Verifying via IPC...")
        self.verification_success_handled = False

        def _timeout():
            if not active_flag[0] or getattr(self, 'verification_success_handled', False): return
            print("[Debug] ⚠️ Verification Timeout (1m). Auto-Skipping...")
            self.status_var.set("⚠️ Verification Timeout: Auto-Skipping...")
            self.action_wipe_and_rotate(is_skip=True)

        self.verification_timer = self.root.after(60000, _timeout)

    def execute_verification_success(self, active_flag):
        if not active_flag[0] or getattr(self, 'verification_success_handled', False): return
        
        self.verification_success_handled = True
        if hasattr(self, 'verification_timer'):
            self.root.after_cancel(self.verification_timer)

        env_vm = os.environ.copy()
        env_vm["DISPLAY"] = MY_DISPLAY

        if getattr(self, 'image_cycle_active', False):
            self.root.after(0, lambda: self.status_var.set("📸 Building Cache..."))
            
            self.extract_token_ipc()
            
            time.sleep(2.0)
            
            subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+shift+w"], env=env_vm)
            
            self.root.after(0, lambda: self.status_var.set("⏳ Writing to Disk (5s)..."))
            time.sleep(5.0)
            
            SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
            golden_cache_path = os.path.join(SCRIPT_DIR, "golden_cache")
            source_cache = os.path.expanduser(f"~/.cache/BraveSoftware/Brave-Browser-{INSTANCE_ID}/Default/Cache/Cache_Data")
            
            print(f" [Image] Copying cache from {source_cache} to {golden_cache_path}")
            subprocess.run(["cp", "-r", source_cache, golden_cache_path])
            
            print(" [Image] Time-shifting the cache by 15 minutes...")
            subprocess.run(["find", golden_cache_path, "-type", "f", "-exec", "touch", "-d", "15 minutes ago", "{}", "+"])
            
            print(" [Image] ✅ Golden Cache creation complete!")
            
            self.root.after(0, lambda: self.action_wipe_and_rotate(is_skip=True, is_image_cycle_end=True))

        else:
            self.root.after(0, lambda: self.status_var.set("✅ Verified! Extracting..."))

            
            self.root.after(0, lambda: self.action_wipe_and_rotate(is_skip=False))

    def extract_token_ipc(self):
        self.status_var.set("Extracting Token via IPC...")
        self.extracted_token_memory = None
        
        self.pending_commands.append({"action": "GET_TOKEN"})
        
        wait_time = 0
        while not getattr(self, 'extracted_token_memory', None) and wait_time < 50:
            time.sleep(0.1)
            wait_time += 1
            
        final_token = getattr(self, 'extracted_token_memory', None)
        if final_token:
            print(f"[IPC] 🔑 Token successfully extracted: {final_token[:15]}...")
            try:
                if self.mode_unclaimed.get(): filename = "verified_tokens_UNCLAIMED.txt"
                elif self.mode_ev.get(): filename = "verified_tokens_EV.txt"
                else: filename = "verified_tokens_FA.txt"
                
                if not os.path.exists(filename): open(filename, 'a').close()
                with open(filename, "r+") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    existing = [l.strip() for l in f.readlines()]
                    
                    if self.mode_unclaimed.get(): line_to_add = f"{final_token}"
                    else: line_to_add = f"{self.current_email} | {self.current_pass} | {final_token}"
                    
                    if line_to_add not in existing:
                        f.seek(0, os.SEEK_END)
                        f.write(line_to_add + "\n")
                    fcntl.flock(f, fcntl.LOCK_UN)
            except Exception as e:
                print(f"[!] File saving error: {e}")
        else:
            print("[IPC] ❌ FATAL ERROR: Failed to extract token within 5 seconds. Destroying the entire tool...")
            os._exit(1)
    
    def internal_extract_token_logic(self):
        possible_paths = [
            os.path.join(MY_DATA_DIR, "Default/Local Storage/leveldb"),
            os.path.join(MY_DATA_DIR, "Profile 1/Local Storage/leveldb")
        ]
        target_path = None
        for p in possible_paths:
            if os.path.exists(p):
                target_path = p
                break
        
        if not target_path: return None

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                subprocess.run(["cp", "-r", target_path + "/.", temp_dir], stderr=subprocess.DEVNULL)
                regex = re.compile(rb'[a-zA-Z0-9_-]{23,}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27,}')
                found_tokens = []
                for filename in os.listdir(temp_dir):
                    fpath = os.path.join(temp_dir, filename)
                    if os.path.isfile(fpath):
                        try:
                            with open(fpath, 'rb') as f:
                                content = f.read()
                                matches = regex.findall(content)
                                for match in matches:
                                    try:
                                        token_str = match.decode(errors='ignore')
                                        if " " not in token_str:
                                            found_tokens.append(token_str)
                                    except: pass
                        except: pass
                if found_tokens:
                    final_token = found_tokens[-1]
                    if final_token.startswith("MT"):
                        try:
                            if self.mode_unclaimed.get():
                                filename = "verified_tokens_UNCLAIMED.txt"
                            elif self.mode_ev.get():
                                filename = "verified_tokens_EV.txt"
                            else:
                                filename = "verified_tokens_FA.txt"
                            
                            if not os.path.exists(filename):
                                open(filename, 'a').close()
                                
                            with open(filename, "r+") as f:
                                fcntl.flock(f, fcntl.LOCK_EX)
                                existing = [l.strip() for l in f.readlines()]
                                
                                if self.mode_unclaimed.get():
                                    line_to_add = f"{final_token}"
                                else:
                                    line_to_add = f"{self.current_email} | {self.current_pass} | {final_token}"
                                    
                                if line_to_add not in existing:
                                    f.seek(0, os.SEEK_END)
                                    f.write(line_to_add + "\n")
                                    
                                fcntl.flock(f, fcntl.LOCK_UN)
                            return final_token
                        except: return None
            except: return None
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = discordAssistant(root)
    root.mainloop()

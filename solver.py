import time
import requests
from requests.auth import HTTPBasicAuth
import websocket
import json
import base64
from io import BytesIO
from PIL import Image

BASE_URL = ""
NGROK_USER = ""
NGROK_PASS = ""

api = requests.Session()
api.auth = HTTPBasicAuth(NGROK_USER, NGROK_PASS) 
api.headers.update({
    "ngrok-skip-browser-warning": "69420",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
})

_auth_string = f"{NGROK_USER}:{NGROK_PASS}"
_encoded_auth = base64.b64encode(_auth_string.encode()).decode()

WS_HEADERS = [
    "ngrok-skip-browser-warning: 69420",
    f"Authorization: Basic {_encoded_auth}"
]


def optimize_b64_image(b64_string, quality=60):
    try:
        prefix = ""
        if "," in b64_string:
            prefix = "data:image/jpeg;base64,"
            b64_string = b64_string.split(",")[1]

        img_data = base64.b64decode(b64_string)
        img = Image.open(BytesIO(img_data))

        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (25, 113, 194)) 
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)

        optimized_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return prefix + optimized_b64 if prefix else optimized_b64

    except Exception as e:
        print(f"⚠️ Image optimization failed: {e}. Sending original.")
        return b64_string

def is_ready():
    try:
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        ws = websocket.create_connection(
            f"{ws_url}/worker_status_ws/", 
            header=WS_HEADERS,
            timeout=5
        )
        data = json.loads(ws.recv())
        ws.close()
        return data.get("online_workers", 0) > 0
    except Exception as e:
        return False

def cancel(task_id):
    """Helper to tell the server to destroy the task and free the worker."""
    try:
        api.post(f"{BASE_URL}/cancel_task/{task_id}/", timeout=5)
    except:
        pass


def solve(captcha_data, task_id, instance_id, is_active=None):
    if is_active is None:
        is_active = [True]
        
    if not is_active[0]:
        print("🛑 Solver aborted: Master Skip signal received before processing.")
        return None

    canvas_base64 = captcha_data.get("canvas")
    question_text = captcha_data.get("question string") or "No question text provided."
    question_img = captcha_data.get("question img") or ""

    if not canvas_base64:
        return {"error": "Missing main image", "type": "error"}

    canvas_base64 = optimize_b64_image(canvas_base64)
    if question_img:
        question_img = optimize_b64_image(question_img)

    print(f"🔄 Sending task {task_id[:6]} (Instance {instance_id}) to API... Waiting for Human via ⚡WebSocket.")

    while True:
        try:
            if not is_active[0]:
                print("🛑 Solver aborted: Task destroyed before sending to server.")
                return None

            response = api.post(f"{BASE_URL}/new_puzzle/", json={
                "task_id": task_id,
                "instance_id": str(instance_id),
                "canvas": canvas_base64,
                "question_string": question_text,
                "question_img": question_img
            }, timeout=5)

            if not response.ok:
                print(f"❌ POST failed! HTTP {response.status_code}: {response.text}")
                response.raise_for_status()
            
            if not is_active[0]:
                print("🛑 Solver aborted: Task destroyed before opening WebSocket.")
                cancel(task_id)
                return None

            ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
            
            ws = websocket.create_connection(
                f"{ws_url}/bot_ws/{task_id}/", 
                header=WS_HEADERS
            )
            
            ws.settimeout(0.5)
            
            timeout = 60
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if not is_active[0]:
                    print(f"🛑 Solver aborted: Task {task_id[:6]} destroyed while waiting for human.")
                    ws.close()
                    cancel(task_id)
                    return None
                    
                try:
                    result_str = ws.recv()
                    data = json.loads(result_str)
                    
                    if data.get("status") == "solved":
                        ws.close()
                        raw_coords = data.get("solution", [])
                        print(f"✅ Human solved task {task_id[:6]}! Received in milliseconds.")
                        
                        if not raw_coords:
                            return {"error": "Human submitted empty solution", "type": "error"}

                        first_action = raw_coords[0]
                        if first_action["type"] == "click":
                            return {"type": "click", "targets": [{"target_x": c["x"], "target_y": c["y"]} for c in raw_coords]}
                        elif first_action["type"] == "drag":
                            return {"type": "drag", "pairs": [{"piece_x": c["startX"], "piece_y": c["startY"], "target_x": c["endX"], "target_y": c["endY"]} for c in raw_coords]}
                    
                    elif data.get("status") == "timeout":
                        ws.close()
                        cancel(task_id)
                        return {"error": "Server reported timeout waiting for human.", "type": "error"}
                            
                except websocket.WebSocketTimeoutException:
                    continue
                except websocket.WebSocketConnectionClosedException:
                    print("⚠️ WebSocket closed unexpectedly. Reconnecting...")
                    break
                
            if time.time() - start_time >= timeout:
                ws.close()
                cancel(task_id)
                return {"error": "Timeout waiting for human.", "type": "error"}
            
        except requests.exceptions.ConnectionError:
            print("⚠️ Could not connect to FastAPI server. Retrying in 2 seconds...")
            time.sleep(2)
            continue
            
        except Exception as e:
            try:
                ws.close()
            except:
                pass
            print(f"⚠️ Unexpected error ({e}). Retrying in 2 seconds...")
            time.sleep(2)
            continue

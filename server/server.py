import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import json
import logging
from fastapi.staticfiles import StaticFiles

class SuppressWebsocketLogs(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "connection open" in msg or "connection closed" in msg or "WebSocket" in msg:
            return False
        return True


app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="static")

USERS = {
    "worker1": {"password": "123", "status": "offline", "last_heartbeat": 0, "sockets": []},
}

MESSAGES = []

class ConnectionManager:
    def __init__(self):
        self.task_queue = []
        self.active_tasks = {}
        self.completed_solutions = {}
        
    async def cancel_task_by_id(self, task_id: str):
        """Called when a user manually clicks skip in the bot UI"""
        self.task_queue = [t for t in self.task_queue if t["task_id"] != task_id]
        
        for username, task in list(self.active_tasks.items()):
            if task["task_id"] == task_id:
                self.active_tasks.pop(username)
                print(f"🗑️ Task {task_id[:6]} cancelled. Clearing '{username}'s screen.", flush=True)
                for ws in USERS[username]["sockets"]:
                    try:
                        await ws.send_text(json.dumps({"type": "clear_task", "task_id": task_id}))
                    except:
                        pass
                await self.assign_tasks()

    async def cancel_task_by_instance(self, instance_id: str):
        """Called automatically when an instance sends a new task, overwriting its old one"""
        self.task_queue = [t for t in self.task_queue if t.get("instance_id") != instance_id]
        
        for username, task in list(self.active_tasks.items()):
            if task.get("instance_id") == instance_id:
                self.active_tasks.pop(username)
                print(f"🔄 Instance {instance_id} sent a new task. Clearing old task from '{username}'.", flush=True)
                for ws in USERS[username]["sockets"]:
                    try:
                        await ws.send_text(json.dumps({"type": "clear_task", "task_id": task["task_id"]}))
                    except:
                        pass
                await self.assign_tasks()
    
    async def assign_tasks(self):
        """Distributes queued tasks to available, online, idle users."""
        available_users = [
            u for u, d in USERS.items() 
            if d["status"] == "online" and len(d["sockets"]) > 0 and u not in self.active_tasks
        ]
        
        while self.task_queue and available_users:
            task = self.task_queue.pop(0)
            user = available_users.pop(0)
            
            task["assigned_at"] = time.time() 
            
            self.active_tasks[user] = task
            
            for client_ws in USERS[user]["sockets"]:
                try:
                    await client_ws.send_text(json.dumps(task))
                except:
                    pass
                    
    async def requeue_if_busy(self, username: str):
        """If a user disconnects or rests while holding a task, put it back in queue."""
        if username in self.active_tasks:
            task = self.active_tasks.pop(username)
            self.task_queue.insert(0, task)
            print(f"♻️ User '{username}' dropped task {task['task_id'][:6]}. Requeued.", flush=True)
            await self.assign_tasks()

    async def handle_message(self, websocket: WebSocket, data: dict, username: str):
        msg_type = data.get("type")

        if msg_type == "heartbeat":
            USERS[username]["last_heartbeat"] = time.time()

        elif msg_type == "set_status":
            new_status = data.get("state")
            if new_status in ["online", "offline"]:
                USERS[username]["status"] = new_status
                USERS[username]["last_heartbeat"] = time.time()
                print(f"👤 User '{username}' is now {new_status.upper()}", flush=True)
                
                if new_status == "offline":
                    await self.requeue_if_busy(username)
                
                for client_ws in USERS[username]["sockets"]:
                    try:
                        await client_ws.send_text(json.dumps({"type": "status_ack", "state": new_status}))
                    except:
                        pass
                        
                if new_status == "online":
                    await self.assign_tasks()

        elif msg_type == "skip_task":
            target_task_id = data.get("task_id")

            if target_task_id and target_task_id in self.completed_solutions:
                print(f"⚠️ Worker '{username}' sent SKIP for already solved task {target_task_id[:6]}. Ignored.", flush=True)
                return

            if username in self.active_tasks:
                task = self.active_tasks[username]
                active_id = task["task_id"]

                if target_task_id and target_task_id != active_id:
                    print(f"⚠️ Stale SKIP from '{username}' (Target: {target_task_id[:6]} != Active: {active_id[:6]}). Ignored.", flush=True)
                    return

                self.active_tasks.pop(username)
                print(f"⏭️ Worker '{username}' triggered remote SKIP on task {active_id[:6]} (Instance {task.get('instance_id')}).", flush=True)
                self.completed_solutions[active_id] = "__SKIPPED__"
                
                for client_ws in USERS[username]["sockets"]:
                    if client_ws != websocket:
                        try:
                            await client_ws.send_text(json.dumps({"type": "clear_task", "task_id": active_id}))
                        except:
                            pass
                
                await self.assign_tasks()

        elif msg_type == "solution":
            target_task_id = data.get("task_id")
            task = self.active_tasks.pop(username, None)
            if task:
                target_task_id = target_task_id or task.get("task_id")

            if target_task_id:
                self.completed_solutions[target_task_id] = data.get("coords")
                
                for client_ws in USERS[username]["sockets"]:
                    if client_ws != websocket:
                        try:
                            await client_ws.send_text(json.dumps({"type": "clear_task", "task_id": target_task_id}))
                        except:
                            pass
            else:
                print(f"⚠️ Solution received from '{username}' but no active task found!", flush=True)

            await self.assign_tasks()

        elif msg_type == "get_online_members":
            online_users = [u for u, d in USERS.items() if d["status"] == "online"]
            try:
                await websocket.send_text(json.dumps({
                    "type": "online_members_list",
                    "members": online_users
                }))
            except:
                pass

        elif msg_type == "get_messages":
            try:
                await websocket.send_text(json.dumps({
                    "type": "messages_update",
                    "messages": MESSAGES
                }))
            except:
                pass
                
        elif msg_type == "post_message":
            text = data.get("text", "").strip()
            if text:
                MESSAGES.append(f"{username}: {text}")
                for u, d in USERS.items():
                    for ws in d["sockets"]:
                        try:
                            await ws.send_text(json.dumps({
                                "type": "messages_update",
                                "messages": MESSAGES
                            }))
                        except:
                            pass
                            
        elif msg_type == "delete_messages":
            MESSAGES.clear()
            for u, d in USERS.items():
                for ws in d["sockets"]:
                    try:
                        await ws.send_text(json.dumps({
                            "type": "messages_update",
                            "messages": MESSAGES
                        }))
                    except:
                        pass

    async def queue_puzzle(self, payload_dict: dict):
        self.task_queue.append(payload_dict)
        await self.assign_tasks()

manager = ConnectionManager()


async def heartbeat_monitor():
    """Runs continuously in the background to kill stale/disconnected sessions."""
    while True:
        now = time.time()
        
        for username, data in USERS.items():
            if data["status"] == "online":
                if now - data["last_heartbeat"] > 30:
                    data["status"] = "offline"
                    print(f"💤 User '{username}' timed out (No heartbeat). Marked OFFLINE.", flush=True)
                    
                    for client_ws in data["sockets"]:
                        try:
                            await client_ws.send_text(json.dumps({"type": "status_ack", "state": "offline"}))
                        except:
                            pass
                    
                    await manager.requeue_if_busy(username)

        for username, task in list(manager.active_tasks.items()):
            if now - task.get("assigned_at", now) > 20:
                print(f"⏱️ User '{username}' took too long! Booting OFFLINE and revoking task.", flush=True)
                
                USERS[username]["status"] = "offline"
                
                for client_ws in USERS[username]["sockets"]:
                    try:
                        await client_ws.send_text(json.dumps({
                            "type": "status_ack", 
                            "state": "offline", 
                            "reason": "timeout"
                        }))
                    except:
                        pass
                
                await manager.requeue_if_busy(username)

        original_queue_size = len(manager.task_queue)
        manager.task_queue = [t for t in manager.task_queue if now - t.get("queued_at", now) < 120]
        
        if len(manager.task_queue) < original_queue_size:
            print(f"🧹 Cleaned {original_queue_size - len(manager.task_queue)} ghost tasks from the queue.", flush=True)

        if len(manager.completed_solutions) > 200:
            keys_to_drop = list(manager.completed_solutions.keys())[:-50]
            for k in keys_to_drop:
                manager.completed_solutions.pop(k, None)
        
        await asyncio.sleep(5)

background_tasks = set()

@app.on_event("startup")
async def startup_event():
    ws_filter = SuppressWebsocketLogs()
    logging.getLogger("uvicorn.error").addFilter(ws_filter)
    logging.getLogger("uvicorn.access").addFilter(ws_filter)

    task = asyncio.create_task(heartbeat_monitor())
    
    background_tasks.add(task)


class PuzzlePayload(BaseModel):
    task_id: str
    instance_id: str
    canvas: str
    question_string: Optional[str] = "No question text provided."
    question_img: Optional[str] = ""

@app.post("/new_puzzle/")
async def receive_puzzle(payload: PuzzlePayload):
    """Bot hits this to add the image to the routing queue"""
    
    await manager.cancel_task_by_instance(payload.instance_id)
    
    await manager.queue_puzzle({
        "type": "new_puzzle",
        "task_id": payload.task_id,
        "instance_id": payload.instance_id,
        "canvas": payload.canvas,
        "question_string": payload.question_string,
        "question_img": payload.question_img,
        "queued_at": time.time()
    })
    return {"status": "success"}

@app.post("/cancel_task/{task_id}/")
async def cancel_task(task_id: str):
    """Bot hits this when 'Skip' is clicked"""
    await manager.cancel_task_by_id(task_id)
    return {"status": "cancelled"}

@app.get("/get_solution/{task_id}/")
async def get_solution(task_id: str):
    """Bot polls this every 0.5s to see if a human is done with ITS specific puzzle"""
    if task_id in manager.completed_solutions:
        sol = manager.completed_solutions.pop(task_id)
        if sol == "__SKIPPED__":
            return {"status": "skipped"}
        return {"status": "solved", "solution": sol}
    return {"status": "waiting"}

@app.websocket("/bot_ws/{task_id}/")
async def bot_websocket(websocket: WebSocket, task_id: str):
    """Dedicated ultra-fast socket for the bot to listen for a specific task."""
    await websocket.accept()
    try:
        for _ in range(1200):
            if task_id in manager.completed_solutions:
                sol = manager.completed_solutions.pop(task_id)
                if sol == "__SKIPPED__":
                    await websocket.send_text(json.dumps({"status": "skipped"}))
                else:
                    await websocket.send_text(json.dumps({"status": "solved", "solution": sol}))
                await websocket.close()
                return
            await asyncio.sleep(0.05)
        
        await websocket.send_text(json.dumps({"status": "timeout"}))
        await websocket.close()
    except WebSocketDisconnect:
        pass

@app.websocket("/worker_status_ws/")
async def worker_status_ws(websocket: WebSocket):
    """Bot polls this via WebSocket to check if there is at least one online screen available"""
    await websocket.accept()
    try:
        online_count = sum(1 for d in USERS.values() if d["status"] == "online" and len(d["sockets"]) > 0)
        await websocket.send_text(json.dumps({"online_workers": online_count}))
        await websocket.close()
    except WebSocketDisconnect:
        pass


@app.get("/")
async def get_portal():
    """Serves the HTML to your phone"""
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time connection with your worker phones"""
    await websocket.accept()
    current_user = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            if data.get("type") == "auth":
                uname = data.get("username")
                pwd = data.get("password")
                
                if uname in USERS and USERS[uname]["password"] == pwd:
                    current_user = uname
                    
                    if websocket not in USERS[uname]["sockets"]:
                        USERS[uname]["sockets"].append(websocket)
                    
                    real_status = USERS[uname]["status"]
                    
                    await websocket.send_text(json.dumps({
                        "type": "auth_success", 
                        "state": real_status
                    }))
                    print(f"🔓 '{uname}' connected a new device. Syncing UI to: {real_status.upper()}", flush=True)
                else:
                    await websocket.send_text(json.dumps({"type": "auth_fail"}))
            
            elif current_user:
                await manager.handle_message(websocket, data, current_user)

    except WebSocketDisconnect:
        if current_user:
            
            if websocket in USERS[current_user]["sockets"]:
                USERS[current_user]["sockets"].remove(websocket)
            
            if len(USERS[current_user]["sockets"]) == 0:
                USERS[current_user]["status"] = "offline"
                
                await manager.requeue_if_busy(current_user)

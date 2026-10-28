import requests
import os
import time
import subprocess
import threading
import queue
import signal
import json
import socket
import re
import select
import base64
import random
import shutil
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse

ROUTER_IP = "192.168.1.1"
BASE_URL = f"https://{ROUTER_IP}"
USERNAME = ""
PASSWORD_B64 = "" 
PPPOE_PASS_HASH = ""
SESSION_FILE = "session_cache.json" 
HISTORY_FILE = "last_mru.txt"

TOKEN_REGEX = re.compile(rb'(?:id="hwonttoken"|name="onttoken")[^>]*value="([a-f0-9]+)"')
SID_REGEX = re.compile(r'(Cookie=sid=[^;]+)')
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

DI_GATEWAY = "gw.dataimpulse.com"
DI_LOGIN = "2e119c6ff10edd638a7b"
DI_PASSWORD = "ce6674bce1860371"
DI_COUNTRY_FILTER = "__cr.de,fr,es,gb,be,bg,ie,us"

class LocalProxyForwarder:
    BLOCKED_WILDCARDS = [
        b".brave.com"
    ]

    def __init__(self, remote_host, remote_port, username, password):
        self.remote_host = remote_host
        self.remote_port = int(remote_port)
        
        self.bytes_uploaded = 0
        self.bytes_downloaded = 0
        self.usage_lock = threading.Lock()
        
        auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.auth_header = f"Proxy-Authorization: Basic {auth_str}\r\n\r\n".encode()
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 0)) 
        self.server.listen(100)
        self.local_port = self.server.getsockname()[1]
        self.running = True
        
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.running:
            try:
                client, _ = self.server.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except:
                break

    def _handle_client(self, client):
        try:
            request = client.recv(8192)
            if not request:
                client.close()
                return

            request_lower = request.lower()
            if any(wildcard in request_lower for wildcard in self.BLOCKED_WILDCARDS):
                client.close()
                return

            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((self.remote_host, self.remote_port))

            modified_request = request.replace(b"\r\n\r\n", b"\r\n" + self.auth_header, 1)
            
            with self.usage_lock:
                self.bytes_uploaded += len(modified_request)
                
            remote.sendall(modified_request)

            self._pipe(client, remote)
        except:
            client.close()

    def _pipe(self, client, remote):
        sockets = [client, remote]
        while self.running:
            r, _, _ = select.select(sockets, [], [], 1)
            if client in r:
                data = client.recv(8192)
                if not data: break
                with self.usage_lock:
                    self.bytes_uploaded += len(data)
                remote.sendall(data)
            if remote in r:
                data = remote.recv(8192)
                if not data: break
                with self.usage_lock:
                    self.bytes_downloaded += len(data)
                client.sendall(data)
        client.close()
        remote.close()
        
    def stop(self):
        self.running = False
        try: self.server.close()
        except: pass


class DataImpulseManager:
    def __init__(self):
        self.state_connected = False
        self.active_forwarders = {}
        self.last_session_kb = 0.0
        print(" [DataImpulse] Initialized Residential Proxy Engine", flush=True)

    def get_ready_proxy(self):
        self.state_connected = True
        
        sticky_port = random.randint(10000, 20000) 
        targeted_username = f"{DI_LOGIN}{DI_COUNTRY_FILTER}"
        
        forwarder = LocalProxyForwarder(DI_GATEWAY, sticky_port, targeted_username, DI_PASSWORD)
        
        slot_id = sticky_port
        self.active_forwarders[slot_id] = forwarder
        
        print(f" [DataImpulse] 🔄 Target Node: {sticky_port} | Local Tunnel: 127.0.0.1:{forwarder.local_port}", flush=True)
        
        return forwarder.local_port, slot_id

    def discard_proxy(self, slot_id):
        """Kills the local TCP port when the cycle ends and logs data usage."""
        if slot_id in self.active_forwarders:
            forwarder = self.active_forwarders[slot_id]
            
            up_kb = forwarder.bytes_uploaded / 1024
            down_kb = forwarder.bytes_downloaded / 1024
            total_kb = up_kb + down_kb
            
            self.last_session_kb = total_kb
            
            forwarder.stop()
            del self.active_forwarders[slot_id]
            
            print(f" [DataImpulse] 🧹 Closed local tunnel for slot {slot_id}", flush=True)
            print(f" 📊 Session Data: [Up: {up_kb:.2f} KB | Down: {down_kb:.2f} KB | Total: {total_kb:.2f} KB]", flush=True)

    def get_last_session_data_usage(self):
        """Returns the total KB of the active session, or the last closed session."""
        if self.active_forwarders:
            forwarder = list(self.active_forwarders.values())[0]
            return (forwarder.bytes_uploaded + forwarder.bytes_downloaded) / 1024
        return self.last_session_kb

    def disconnect(self):
        self.state_connected = False
        for slot_id in list(self.active_forwarders.keys()):
            self.discard_proxy(slot_id)

    def is_active(self):
        return self.state_connected

proxy_engine = DataImpulseManager()

def get_upnp_ip():
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_MX = 1
    SSDP_ST = "urn:schemas-upnp-org:service:WANIPConnection:1"
    ssdp_msg = ('M-SEARCH * HTTP/1.1\r\n' + f'HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n' + 'MAN: "ssdp:discover"\r\n' + f'MX: {SSDP_MX}\r\n' + f'ST: {SSDP_ST}\r\n\r\n')

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        sock.sendto(ssdp_msg.encode(), (SSDP_ADDR, SSDP_PORT))
        data, addr = sock.recvfrom(1024)
        response = data.decode()
        location = re.search(r'LOCATION: (http://.+)', response, re.IGNORECASE)
        if not location: return None
        desc_url = location.group(1).strip()
        try:
            r = requests.get(desc_url, timeout=1)
            control_url_match = re.search(r'<controlURL>(.*?)</controlURL>', r.text)
            if control_url_match:
                control_path = control_url_match.group(1)
                if "http" not in control_path:
                    parsed = urlparse(desc_url)
                    control_url = f"{parsed.scheme}://{parsed.netloc}{control_path}"
                else: control_url = control_path
            else: return None
        except: return None

        soap_body = """<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:GetExternalIPAddress xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"></u:GetExternalIPAddress></s:Body></s:Envelope>"""
        headers = {'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#GetExternalIPAddress"', 'Content-Type': 'text/xml'}
        r_soap = requests.post(control_url, data=soap_body, headers=headers, timeout=1)
        ip_match = re.search(r'<NewExternalIPAddress>(.*?)</NewExternalIPAddress>', r_soap.text)
        if ip_match: return ip_match.group(1).strip()
    except: pass
    return None

def get_public_ip():
    ip = get_upnp_ip()
    if ip and ip != "0.0.0.0": return ip
    try:
        r = requests.get("https://api.ipify.org", timeout=1.5)
        if r.status_code == 200 and len(r.text) > 4: return r.text.strip()
    except: pass
    return None

def wait_for_internet(timeout=15):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=0.8)
            return True
        except OSError: time.sleep(0.1)
    return False

def get_session():
    s = requests.Session()
    s.verify = False
    s.mount("https://", HTTPAdapter(pool_connections=1, pool_maxsize=1))
    s.headers = {"User-Agent": "Mozilla/5.0", "Referer": f"{BASE_URL}/", "Connection": "keep-alive"}
    return s

def perform_rotation(s, auth_cookie, action_token):
    last_mru = 0
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                content = f.read().strip()
                if content.isdigit(): last_mru = int(content)
        except: pass
    new_mru = random.choice([x for x in range(1480, 1501) if x != last_mru])
    url = f"{BASE_URL}/html/bbsp/wan/complex.cgi?y=InternetGatewayDevice.WANDevice.2.WANConnectionDevice.1.WANPPPConnection.1&e=InternetGatewayDevice.WANDevice.2.WANConnectionDevice.1.WANPTMLinkConfig&RequestFile=html/bbsp/wan/confirmwancfginfo.html"
    try:
        r = s.post(url, headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": auth_cookie}, 
                   data={"y.Enable": "1", "y.ConnectionType": "IP_Routed", "y.NATEnabled": "1", "y.Username": "LAND_LINE@Orange", 
                         "y.Password": PPPOE_PASS_HASH, "y.MaxMRUSize": str(new_mru), "x.X_HW_Token": action_token}, timeout=6)
        if r.status_code == 200:
            with open(HISTORY_FILE, "w") as f: f.write(str(new_mru))
            return 200
    except requests.exceptions.ReadTimeout: return 200
    return 0

def rotate_ip_guaranteed(force_proxy=False):
    
    if force_proxy:
        print(" [Config] 🚫 Router Disabled. Utilizing DataImpulse Sticky Ports.")
        proxy_engine.state_connected = True
        return True

    proxy_engine.disconnect()

    print("[*] Checking IP (UPnP Mode)...")
    old_ip = get_public_ip()
    
    while not old_ip:
        print("[!] Internet down, waiting...")
        time.sleep(0.2) 
        old_ip = get_public_ip()
    
    print(f"[*] Current IP: {old_ip}")
    s = get_session()
    
    while True:
        auth_cookie, action_token = None, None
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                    auth_cookie, action_token = data["cookie"], data["token"]
            except: pass

        success = False
        if auth_cookie:
            if perform_rotation(s, auth_cookie, action_token) == 200: success = True

        if not success:
            try:
                r1 = s.post(f"{BASE_URL}/asp/GetRandCount.asp", headers={"X-Requested-With": "XMLHttpRequest"}, timeout=3)
                login_token = re.sub(rb'[^a-fA-F0-9]', b'', r1.content).decode()
                r2 = s.post(f"{BASE_URL}/login.cgi", data={"UserName": USERNAME, "PassWord": PASSWORD_B64, "Language": "english", "x.X_HW_Token": login_token}, stream=True, timeout=3)
                auth_cookie = SID_REGEX.search(r2.headers.get("Set-Cookie", "")).group(1)
                r2.close() 
                r3 = s.get(f"{BASE_URL}/html/bbsp/wan/wan.asp", headers={"Cookie": auth_cookie}, timeout=3)
                action_token = TOKEN_REGEX.search(r3.content).group(1).decode()
                with open(SESSION_FILE, "w") as f: json.dump({"cookie": auth_cookie, "token": action_token}, f)
                if perform_rotation(s, auth_cookie, action_token) == 200: success = True
            except:
                time.sleep(0.2)
                continue

        if success:
            if wait_for_internet():
                new_ip = get_public_ip()
                if new_ip:
                    if new_ip != old_ip:
                        if new_ip.startswith(("42.", "35.")):
                            print(f" ⚠️  UNDESIRED IP Detected ({new_ip}). Engaging proxy Pool...")
                            proxy_engine.state_connected = True
                            return True
                        
                        print(f"[SUCCESS] IP Changed: {old_ip} -> {new_ip}")
                        return True
                    else:
                        print(f"[!] IP stayed the same ({new_ip}). Retrying MRU...")
                else:
                    print("[!] Internet up but IP Check failed. Retrying...")
            else:
                print("[!] Reconnection timeout.")
                return False

if __name__ == "__main__":
    rotate_ip_guaranteed()

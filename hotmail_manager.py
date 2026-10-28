import requests
import re
import time
import urllib3
import json
import imaplib
import email
import os
import socket
import ssl
import struct
import random
import sys
import threading
from email.header import decode_header
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection 
from urllib3.util import connection

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ZEUS_API_KEY = "fdaf478fb47e4b1fa91318f31b79dbcd"
ZEUS_BUY_URL = "https://api.zeus-x.ru/purchase"

LUTION_API_KEY = "b99416c5f733aba74ac9abb1a886be0b"
LUTION_BUY_URL = "https://lution.ee/api/v2/email/buy"

ACTIVE_PROVIDER = "lution" 

try:
    INSTANCE_ID = int(sys.argv[1])
except:
    INSTANCE_ID = 1

TOKEN_ENDPOINT = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

ALLOW_FA_RESERVE = True 
RESERVE_THREADS = 10
RESERVE_LIMIT = 10
_file_lock = threading.Lock()

def get_reserve_filepath(mode):
    return f"unused_emails_{mode}_{INSTANCE_ID}.json"

def _perform_raw_purchase(mode):
    """
    Directly hits the active API to buy 1 account. 
    """
    if ACTIVE_PROVIDER == "lution":
        search_types = ["hotmail", "outlook"] if mode == "EV" else ["hotmail.trusted.graph", "outlook.trusted.graph"]
        random.shuffle(search_types)
        
        session = requests.Session()
        headers = {
            "Authorization": f"Bearer {LUTION_API_KEY}",
            "Content-Type": "application/json"
        }
        
        for svc_code in search_types:
            payload = { "category": svc_code, "quantity": 1 }
            try:
                resp = session.post(LUTION_BUY_URL, headers=headers, json=payload, verify=False, timeout=5)
                if resp.status_code in [200, 201]:
                    try: json_data = resp.json()
                    except: continue

                    if json_data.get("success"):
                        data_block = json_data.get("data", {})
                        acc_data = {}
                        if isinstance(data_block, list) and len(data_block) > 0: 
                            acc_data = data_block[0]
                        elif isinstance(data_block, dict): 
                            nested = data_block.get("emails", data_block.get("accounts", []))
                            if isinstance(nested, list) and len(nested) > 0: acc_data = nested[0]
                            else: acc_data = data_block

                        email_val = acc_data.get("email", acc_data.get("Email"))
                        pass_val = acc_data.get("password", acc_data.get("Password"))

                        if not email_val or not pass_val: continue

                        raw_string = acc_data.get("full_string", f"{email_val}:{pass_val}")
                        found_token = acc_data.get("refresh_token") or acc_data.get("graph_refresh_token") or acc_data.get("token")
                        
                        client_id = acc_data.get("thunderbird_client_id") or acc_data.get("client_id") or "9e5f94bc-e8a4-4e73-b8be-63364c29d753"

                        print(f" [Bg] ✅ Successfully sniped {svc_code} from Lution!")
                        return { 
                            "valid": True, 
                            "email": email_val, 
                            "password": pass_val, 
                            "full_string": raw_string,
                            "type": svc_code,
                            "mode": mode,
                            "refresh_token": found_token,
                            "client_id": client_id
                        }
            except Exception: continue
        return None

    elif ACTIVE_PROVIDER == "zeus":
        search_types = ["OUTLOOK", "HOTMAIL"] if mode == "EV" else ["HOTMAIL_TRUSTED"]
        if len(search_types) > 1: random.shuffle(search_types)

        for svc_code in search_types:
            params = { "apikey": ZEUS_API_KEY, "accountcode": svc_code, "quantity": 1 }
            try:
                resp = requests.get(ZEUS_BUY_URL, params=params, verify=False, timeout=5)
                if resp.status_code == 200:
                    try: json_data = resp.json()
                    except: continue 
                    
                    code_val = json_data.get("Code") if "Code" in json_data else json_data.get("code")
                    if code_val == 0:
                        data_block = json_data.get("Data") or json_data.get("data")
                        acc_data = {}
                        if isinstance(data_block, dict) and "Accounts" in data_block:
                            accs = data_block["Accounts"]
                            if isinstance(accs, list) and len(accs) > 0: acc_data = accs[0]
                        elif isinstance(data_block, list) and len(data_block) > 0:
                            if isinstance(data_block[0], dict): acc_data = data_block[0]

                        if acc_data.get("Email") and acc_data.get("Password"):
                            if not acc_data.get("ClientId"):
                                acc_data["ClientId"] = "8b4ba9dd-3ea5-4e5f-86f1-ddba2230dcf2" 

                            raw_string = acc_data.get("full_string", f"{acc_data.get('Email')}:{acc_data.get('Password')}")
                            found_token = acc_data.get("RefreshToken") or acc_data.get("refresh_token") or acc_data.get("token")
                            
                            if not found_token:
                                parts = raw_string.split(":")
                                if len(parts) >= 3:
                                    found_token = parts[-1] if len(parts[-1]) > 30 else parts[2]

                            print(f" [Bg] ✅ Successfully sniped {svc_code} from Zeus!")
                            return { 
                                "valid": True, 
                                "email": acc_data.get("Email"), 
                                "password": acc_data.get("Password"), 
                                "full_string": raw_string,
                                "type": svc_code,
                                "mode": mode,
                                "refresh_token": found_token,
                                "client_id": acc_data.get("ClientId")
                            }
            except Exception: continue
        return None
    
    return None

def _reserve_loop(mode):
    target_file = get_reserve_filepath(mode)
    
    if not os.path.exists(target_file):
        with open(target_file, 'w') as f: json.dump([], f)

    while True:
        try:
            with _file_lock:
                try:
                    with open(target_file, 'r') as f:
                        content = f.read().strip()
                        current_stock = json.loads(content) if content else []
                except (json.JSONDecodeError, FileNotFoundError):
                    current_stock = []
                    with open(target_file, 'w') as f: json.dump([], f)

            if len(current_stock) < RESERVE_LIMIT:
                new_acc = _perform_raw_purchase(mode)
                
                if new_acc and new_acc.get("valid"):
                    with _file_lock:
                        try:
                            with open(target_file, 'r') as f:
                                fresh_stock = json.load(f)
                        except: fresh_stock = []

                        fresh_stock.append(new_acc)
                        
                        with open(target_file, "w") as f:
                            json.dump(fresh_stock, f, indent=4)
                            
                        print(f"[Bg] ⚡ SNIPED! Total {mode} stock is now: {len(fresh_stock)}")
            else:
                time.sleep(0.5)
        except Exception:
            time.sleep(0.5)

def start_reserve_keeper(mode, num_threads=RESERVE_THREADS):
    base_name = f"ReserveKeeper_{mode}_{INSTANCE_ID}"
    
    if any(t.name.startswith(base_name) for t in threading.enumerate()):
        return
        
    print(f"\n[🚀] DEPLOYING SWARM: {num_threads} concurrent snipers active for Instance {INSTANCE_ID}...\n")
    
    for i in range(num_threads):
        t = threading.Thread(target=_reserve_loop, args=(mode,), daemon=True, name=f"{base_name}_{i}")
        t.start()


def buy_account(mode="FA"):
    SERVICE_CODE = "HOTMAIL_TRUSTED" if mode == "FA" else "OUTLOOK"
    dynamic_saved_file = f"saved_emails_{mode}_{INSTANCE_ID}.json"

    if os.path.exists(dynamic_saved_file):
        try:
            print(f"[*] Loading account from {dynamic_saved_file}...")
            with open(dynamic_saved_file, "r") as f:
                accounts = json.load(f)
            
            if isinstance(accounts, list) and len(accounts) > 0:
                random_index = random.randint(0, len(accounts) - 1)
                acc_data = accounts.pop(random_index) 
                
                with open(dynamic_saved_file, "w") as f:
                    json.dump(accounts, f, indent=4)
                
                print(f"    [+] Loaded & Removed: {acc_data.get('Email') or acc_data.get('email')}")
                print(f"    [+] Remaining in file: {len(accounts)}")
                
                return { 
                    "valid": True, 
                    "email": acc_data.get("Email") or acc_data.get("email"), 
                    "password": acc_data.get("Password") or acc_data.get("password"), 
                    "full_string": acc_data.get("full_string") or f"{acc_data.get('Email')}:{acc_data.get('Password')}",
                    "type": SERVICE_CODE,
                    "mode": mode,
                    "refresh_token": acc_data.get("RefreshToken") or acc_data.get("refresh_token"),
                    "client_id": acc_data.get("ClientId") or acc_data.get("client_id") or "8b4ba9dd-3ea5-4e5f-86f1-ddba2230dcf2"
                }
            else:
                print("    [!] Local file is empty.")
        except Exception as e:
            print(f"[!] Error handling local file: {e}")

    if mode == "EV" or (mode == "FA" and ALLOW_FA_RESERVE):
        start_reserve_keeper(mode=mode)
        target_reserve = get_reserve_filepath(mode)
        
        with _file_lock:
            if os.path.exists(target_reserve):
                try:
                    with open(target_reserve, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list) and len(data) > 0:
                        reserve_acc = data.pop(0)
                        
                        with open(target_reserve, 'w') as f:
                            json.dump(data, f, indent=4)
                            
                        print(f"\n[*] Account retrieved from {mode} Reserve JSON: {reserve_acc.get('email')}")
                        return reserve_acc 
                except: pass

    print(f"[*] Reserve empty/unavailable. Purchasing directly from Zeus (Code: {SERVICE_CODE})...")
    acc_data = _perform_raw_purchase(mode)
    
    if acc_data and acc_data.get("valid"):
        return acc_data

    return {"valid": False}

def get_access_token(refresh_token, client_id, use_graph=False):
    print("    [*] Exchanging Refresh Token...")
    
    session = requests.Session()

    headers = {
        'Host': 'login.microsoftonline.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    data = {
        "client_id": client_id,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    if "9e5f94bc" in client_id:
        data["scope"] = "https://graph.microsoft.com/.default"
    else:
        data["scope"] = "https://outlook.office.com/.default"

    try:
        rr = session.post(TOKEN_ENDPOINT, headers=headers, data=data, timeout=5)
        json_resp = rr.json()
        
        if json_resp.get("error") is None:
            print("    [+] Token Acquired.")
            return json_resp["access_token"]
        elif "User account is found to be in service abuse mode" in json_resp.get("error_description", ""):
            print("    [!] Account is Blocked/Abuse Mode.")
        else:
            print(f"    [!] Token Error: {json_resp.get('error_description')}")
            
    except Exception as e:
        print(f"    [!] Token Net Error: {e}")
    return None

def imap_authenticate_with_oauth2(username, access_token):
    """
    Connects to Outlook IMAP via PHYSICAL INTERFACE.
    """
    auth_string = f"user={username}\1auth=Bearer {access_token}\1\1"
    
    for attempt in range(1, 11):
        print(f"    [*] Connecting to Outlook IMAP... (Attempt {attempt}/10)")
        
        try:
            mail = imaplib.IMAP4_SSL("outlook.office365.com", timeout=5)
            mail.authenticate("XOAUTH2", lambda x: auth_string)
            return mail
        except Exception as e:
            print(f"    [!] IMAP Connection Failed: {e}")
            if attempt < 10:
                time.sleep(1)
            else:
                return None
    return None

def get_verification_link(account_input, mode="FA"):
    email_user = None
    refresh_token = None
    client_id = None

    if isinstance(account_input, dict):
        email_user = account_input.get("email")
        mode = account_input.get("mode", mode)
        refresh_token = account_input.get("refresh_token")
        client_id = account_input.get("client_id")
    elif isinstance(account_input, str):
        parts = account_input.split(":")
        if len(parts) >= 2: email_user = parts[0]

    if not email_user: return None

    print(f"[*] Checking inbox for: {email_user} (Mode: {mode})")

    is_graph = (mode == "EV")
    
    if ACTIVE_PROVIDER == "lution":
        is_graph = True

    if not client_id:
        if is_graph:
            client_id = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"
        else:
            client_id = "8b4ba9dd-3ea5-4e5f-86f1-ddba2230dcf2"

    access_token = None
    if refresh_token and client_id:
        access_token = get_access_token(refresh_token, client_id, use_graph=is_graph)
    
    if not access_token:
        print("    [!] Failed to get Access Token.")
        return None

    if is_graph:
        return _poll_graph_api(access_token, client_id) 
    else:
        return _poll_imap(email_user, access_token)

def _poll_graph_api(access_token, client_id):
    print("    [*] Connection established (REST/Graph API). Waiting for email...")
    
    if "9e5f94bc" in client_id:
        base_url = "https://graph.microsoft.com/v1.0"
        filter_query = "?$filter=isRead eq false&$orderby=receivedDateTime desc&$top=5"
    else:
        base_url = "https://outlook.office.com/api/v2.0"
        filter_query = "?$filter=IsRead eq false&$orderby=ReceivedDateTime desc&$top=5"

    headers = {"Authorization": f"Bearer {access_token}"}
    folders_to_check = ["inbox", "junkemail"]
    
    found_link = None
    start_time = time.time()
    printed_empty = False
    
    try:
        while time.time() - start_time < 10: 
            for folder in folders_to_check:
                url = f"{base_url}/me/mailfolders/{folder}/messages{filter_query}"
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code != 200: continue

                    messages = response.json().get("value", [])
                    if not messages: continue

                    for msg_data in messages:
                        sender_obj = msg_data.get("from") or msg_data.get("sender") or {}
                        email_obj = sender_obj.get("emailAddress") or sender_obj.get("EmailAddress") or {}
                        sender = email_obj.get("address") or email_obj.get("Address") or ""
                        
                        if "discord.com" in sender.lower():
                            msg_id = msg_data.get("id") or msg_data.get("Id")
                            mime_url = f"{base_url}/me/messages/{msg_id}/$value"
                            mime_resp = requests.get(mime_url, headers=headers, timeout=5)
                            
                            if mime_resp.status_code == 200:
                                raw_msg = email.message_from_bytes(mime_resp.content)
                                body = _get_body(raw_msg)
                                link = _extract_link(body)
                                if link:
                                    print(f"    [+] (REST API - {folder.upper()}) Link Found via MIME")
                                    return link
                            
                            fallback_body = msg_data.get("body", {}).get("content", "")
                            if fallback_body:
                                link = _extract_link(fallback_body)
                                if link:
                                    print(f"    [+] (REST API - {folder.upper()}) Link Found via Fallback HTML")
                                    return link
                                
                except requests.exceptions.RequestException: pass
            
            if not printed_empty:
                print(f"    [DEBUG] Connected successfully, scanning Inbox & JunkEmail...")
                printed_empty = True
            time.sleep(0.5) 
            
    except KeyboardInterrupt:
         print("\n    [!] Stopped by user.")
         
    if not found_link: print("    [!] Verification email never arrived (Timed out).")
    return found_link

def _poll_imap(email_user, access_token):
    try:
        mail = imap_authenticate_with_oauth2(email_user, access_token)
    except Exception as e:
        print(f"    [!] Initial Connection Failed: {e}")
        return None

    if not mail: return None

    print("    [*] Connection established (IMAP). Waiting for email (Instant Mode)...")

    found_link = None
    start_time = time.time()
    
    try:
        for _ in range(10):
            try:
                mail.select("inbox") 
                break
            except:
                time.sleep(0.2)
        
        while time.time() - start_time < 10:
            try:
                link = _search_messages(mail, "Inbox")
                if link:
                    found_link = link
                    break 
                
                time.sleep(0.5)

            except (imaplib.IMAP4.abort, socket.error):
                print(f"\n    [!] Connection dropped. Reconnecting...")
                try:
                    mail = imap_authenticate_with_oauth2(email_user, access_token)
                    mail.select("inbox")
                except: break
            except KeyboardInterrupt:
                break
                
    except KeyboardInterrupt:
        print("\n    [!] Stopped by user.")
    finally:
        try:
            mail.logout()
        except: pass

    if not found_link:
        print("[!] Verification email never arrived (Timed out).")

    return found_link

def _search_messages(mail, folder_name):
    try:
        status, messages = mail.search(None, '(UNSEEN FROM "discord.com")')
        
        if status != "OK": return None
        msg_ids = messages[0].split()
        if not msg_ids: return None

        for m_id in reversed(msg_ids[-1:]):
            _, msg_data = mail.fetch(m_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = _get_body(msg)
                    link = _extract_link(body)
                    if link:
                        print(f"[+] ({folder_name}) Link Found")
                        return link
    except Exception as e:
        pass
    return None

def _get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/html", "text/plain"]:
                payload = part.get_payload(decode=True)
                if payload: body += payload.decode(errors='ignore')
    else:
        payload = msg.get_payload(decode=True)
        if payload: body = payload.decode(errors='ignore')
    return body

def _extract_link(text):
    if not text: return None
    match = re.search(r'(https?://click\.discord\.com[^\s"\'<>]+)', text)
    if match: return match.group(1).replace('"', '').replace('&amp;', '&')
    match = re.search(r'href=\\?"(https?://[^\s"\\]+)\\?"[^>]*>\s*Verify Email', text)
    if match: return match.group(1).replace('"', '').replace('&amp;', '&')
    return None

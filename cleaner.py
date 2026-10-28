import os
import shutil
import time
import subprocess
import json
import random
import string
import sys

try:
    INSTANCE_ID = int(sys.argv[1])
except:
    INSTANCE_ID = 1

HOME_DIR = os.path.expanduser("~")
BRAVE_CONFIG_ROOT = os.path.join(HOME_DIR, f".config/BraveSoftware/Brave-Browser-{INSTANCE_ID}")
BRAVE_DEFAULT_DIR = os.path.join(BRAVE_CONFIG_ROOT, "Default")
BRAVE_CACHE_ROOT = os.path.join(HOME_DIR, f".cache/BraveSoftware/Brave-Browser-{INSTANCE_ID}")

def force_kill_brave():
    """Stops the specific instance's Brave processes."""
    subprocess.run(["pkill", "-9", "-f", f"user-data-dir={BRAVE_CONFIG_ROOT}"], stderr=subprocess.DEVNULL)
    time.sleep(0.1)

def generate_random_id(length=32):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def rotate_browser_identity():
    """
    Modifies 'Local State' in the ROOT folder.
    """
    local_state_path = os.path.join(BRAVE_CONFIG_ROOT, "Local State")
    if not os.path.exists(local_state_path): return

    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'user_experience_metrics' in data:
            data['user_experience_metrics']['client_id'] = generate_random_id(36)
            data['user_experience_metrics']['timestamp_metrics_reporting_enabled'] = str(int(time.time()))
        
        if 'signin' in data and 'device_id' in data['signin']:
            data['signin']['device_id'] = f"device_id_{generate_random_id(10)}"
        
        if 'variations_compressed_seed' in data:
            del data['variations_compressed_seed']

        with open(local_state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
    except Exception as e:
        print(f" [!] Warning: Could not randomize Identity: {e}")

def perform_deep_clean(mode="FA"):
    if os.geteuid() == 0:
        print(" [WARNING] You are running as ROOT! For optimal stealth, run as a standard user.")

    print(f"\n [CLEANER] Cleaning Profile for Instance {INSTANCE_ID}...")
    force_kill_brave()
    
    targets_default = [
        "Cookies", "Cookies-journal", 
        "Local Storage", "Service Worker", 
        "Session Storage", "Sessions", 
        "IndexedDB", "History", "History-journal", 
        "Web Data", "Web Data-journal",
        "Extension State", "Platform Notifications", 
        "QuotaManager", "Network Persistent State",
        "Network",
        
        "Trust Tokens", "Trust Tokens-journal",
        "GPUCache", 
        "DawnGraphiteCache", 
        "DawnWebGPUCache",
        "DIPS", "DIPS-journal",
        "MediaDeviceSalts", "MediaDeviceSalts-journal",
        "Network Action Predictor", "Network Action Predictor-journal",
        "Reporting and NEL", "Reporting and NEL-journal",
        "CdmStorage.db", "CdmStorage.db-journal",
        "WebStorage"
    ]
    
    if os.path.exists(BRAVE_DEFAULT_DIR):
        for item in targets_default:
            path = os.path.join(BRAVE_DEFAULT_DIR, item)
            if os.path.exists(path):
                try:
                    if os.path.isfile(path): os.remove(path)
                    else: shutil.rmtree(path)
                except: pass

    targets_toplevel = [
        "GrShaderCache",
        "GraphiteDawnCache"
    ]
    
    for item in targets_toplevel:
        path = os.path.join(BRAVE_CONFIG_ROOT, item)
        if os.path.exists(path):
            try:
                if os.path.isfile(path): os.remove(path)
                else: shutil.rmtree(path)
            except: pass

    code_cache_dir = os.path.join(BRAVE_CACHE_ROOT, "Default", "Code Cache")
    if os.path.exists(code_cache_dir):
        try:
            shutil.rmtree(code_cache_dir)
            print(" [+] Sanitized: Destroyed V8 Code Cache")
        except Exception as e:
            print(f" [-] Failed to delete Code Cache: {e}")

    cache_base = os.path.join(BRAVE_CACHE_ROOT, "Default", "Cache")
    cache_data_dir = os.path.join(cache_base, "Cache_Data")
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    if mode == "UNCLAIMED":
        target_cache_name = "golden_cache_unclaimed"
    elif mode == "TRIAL":
        target_cache_name = "golden_cache_trial"
    else:
        target_cache_name = "golden_cache"

    golden_cache_path = os.path.join(SCRIPT_DIR, target_cache_name)

    if os.path.exists(cache_base):
        subprocess.run(["chmod", "-R", "777", cache_base], stderr=subprocess.DEVNULL)
        
    if os.path.exists(cache_data_dir):
        subprocess.run(["rm", "-rf", cache_data_dir])

    if os.path.exists(golden_cache_path):
        os.makedirs(cache_base, exist_ok=True)
        print(f" [+] Injecting Aged Golden Cache from {golden_cache_path}...")
        subprocess.run(["cp", "-r", golden_cache_path, cache_data_dir])
        
        subprocess.run(["chmod", "-R", "777", cache_data_dir])
        print(" [+] Cache Injected and Unlocked. Brave is ready to boot.")
    else:
        print(f" [!] Golden Cache not found at {golden_cache_path}! Proceeding with blank cache.")

    trust_tokens_path = os.path.join(BRAVE_DEFAULT_DIR, "Trust Tokens")
    dips_path = os.path.join(BRAVE_DEFAULT_DIR, "DIPS")
    
    for path in [trust_tokens_path, dips_path]:
        if os.path.exists(path):
            try:
                if os.path.isfile(path): os.remove(path)
                else: shutil.rmtree(path)
            except: pass

    rotate_browser_identity()

    print(f" [Cleaner] ✅ Profile {INSTANCE_ID} Cleaned.")

if __name__ == "__main__":
    perform_deep_clean()

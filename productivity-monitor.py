#!/usr/bin/env python3

import subprocess
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Configuration
POKE_API_KEY = "YOUR_POKE_API_KEY"  # Get your key at https://poke.com/settings/advanced
POKE_API_URL = "https://poke.com/api/v1/inbound-sms/webhook"
QUEUE_FILE = Path("/tmp/productivity_queue.json")
STATE_FILE = Path("/tmp/productivity_state.json")
BATCH_INTERVAL = 1800  # 30 minutes
CHECK_INTERVAL = 10  # seconds

# Apps to ignore (too noisy or not relevant)
IGNORED_APPS = {
    "Finder", "System Settings", "System Preferences", "loginwindow",
    "Dock", "Spotlight", "Control Center", "NotificationCenter"
}

def send_to_poke(message):
    """Send message to Poke via API"""
    try:
        response = requests.post(
            POKE_API_URL,
            headers={
                'Authorization': f'Bearer {POKE_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={'message': message},
            timeout=10
        )
        return response.json()
    except Exception as e:
        # Log error but don't crash
        with open('/tmp/productivity.err', 'a') as f:
            f.write(f"Error sending to Poke: {e}\n")
        return None

def load_queue():
    """Load event queue from disk"""
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_queue(queue):
    """Save event queue to disk"""
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f)

def load_state():
    """Load previous state from disk"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_app": None,
        "last_window": None,
        "last_focus": None,
        "last_wifi": None,
        "last_bluetooth": [],
        "last_battery_alert": 0,
        "last_posture_alert": 0,
        "active_start_time": time.time(),
        "meeting_process": None,
        "meeting_start": None
    }

def save_state(state):
    """Save current state to disk"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def add_event(event_type, description):
    """Add event to queue with timestamp"""
    queue = load_queue()
    timestamp = datetime.now().strftime("%H:%M")
    queue.append({
        "time": timestamp,
        "type": event_type,
        "description": description,
        "timestamp_full": time.time()
    })
    save_queue(queue)

def get_active_app():
    """Get frontmost application name"""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()

def get_window_title():
    """Get frontmost window title"""
    script = '''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        tell frontApp
            if exists (1st window whose value of attribute "AXMain" is true) then
                set windowTitle to value of attribute "AXTitle" of (1st window whose value of attribute "AXMain" is true)
                return windowTitle
            end if
        end tell
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    title = result.stdout.strip()
    return title if title else None

def get_focus_mode():
    """Check if Focus/Do Not Disturb is enabled"""
    result = subprocess.run(
        ["defaults", "read", "com.apple.controlcenter", "NSStatusItem Visible FocusModes"],
        capture_output=True, text=True
    )
    # This is a heuristic - true presence often means enabled
    return "1" in result.stdout or result.returncode == 0

def get_wifi_ssid():
    """Get current WiFi SSID"""
    result = subprocess.run(
        ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
        capture_output=True, text=True
    )
    for line in result.stdout.split('\n'):
        if ' SSID:' in line:
            return line.split('SSID:')[1].strip()
    return None

def get_bluetooth_devices():
    """Get connected Bluetooth devices"""
    result = subprocess.run(
        ["system_profiler", "SPBluetoothDataType", "-json"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        devices = []
        if 'SPBluetoothDataType' in data:
            for item in data['SPBluetoothDataType']:
                if 'device_connected' in item:
                    for device_list in item.get('device_connected', []):
                        devices.extend(device_list.keys())
        return devices
    except:
        return []

def get_battery_level():
    """Get battery percentage"""
    result = subprocess.run(
        ["pmset", "-g", "batt"],
        capture_output=True, text=True
    )
    for line in result.stdout.split('\n'):
        if '%' in line:
            try:
                percent = int(line.split('%')[0].split()[-1])
                return percent
            except:
                pass
    return None

def get_meeting_process():
    """Check if video meeting app is running"""
    result = subprocess.run(["pgrep", "-i", "zoom|meet|teams|webex"], capture_output=True, text=True)
    if result.returncode == 0:
        # Try to identify which one
        for app in ["zoom.us", "Google Meet", "Microsoft Teams", "Webex"]:
            check = subprocess.run(["pgrep", "-i", app.replace(" ", "")], capture_output=True)
            if check.returncode == 0:
                return app
        return "Video Meeting"
    return None

def send_batch():
    """Send batched events as a single message"""
    queue = load_queue()
    if not queue:
        return
    
    # Get time range
    start_time = queue[0]["time"]
    end_time = queue[-1]["time"]
    
    # Format message with ALL events
    header = f"This is an automated message being sent to you from Mac through your Poke API\n📊 Activity Update ({start_time}-{end_time}):"
    events = [f"• {item['time']} - {item['description']}" for item in queue]  # Send ALL events
    
    message = header + "\n" + "\n".join(events)
    send_to_poke(message)
    
    # Clear queue
    save_queue([])

def main():
    """Main monitoring loop"""
    state = load_state()
    last_batch_time = time.time()
    
    while True:
        current_time = time.time()
        
        # Check if it's time to send batch
        if current_time - last_batch_time >= BATCH_INTERVAL:
            send_batch()
            last_batch_time = current_time
        
        # Monitor active app
        try:
            app = get_active_app()
            if app and app not in IGNORED_APPS and app != state["last_app"]:
                add_event("app", f"Switched to {app}")
                state["last_app"] = app
        except:
            pass
        
        # Monitor window title (only for productive apps)
        try:
            if state["last_app"] and state["last_app"] not in IGNORED_APPS:
                window = get_window_title()
                if window and window != state["last_window"] and len(window) < 100:
                    add_event("window", f"Working on: {window}")
                    state["last_window"] = window
        except:
            pass
        
        # Monitor focus mode (every 30s)
        if int(current_time) % 30 == 0:
            try:
                focus = get_focus_mode()
                if focus != state["last_focus"]:
                    status = "enabled" if focus else "disabled"
                    add_event("focus", f"Focus Mode {status}")
                    state["last_focus"] = focus
            except:
                pass
        
        # Monitor WiFi (every 30s)
        if int(current_time) % 30 == 0:
            try:
                wifi = get_wifi_ssid()
                if wifi and wifi != state["last_wifi"]:
                    add_event("wifi", f"Connected to: {wifi}")
                    state["last_wifi"] = wifi
            except:
                pass
        
        # Monitor Bluetooth (every 30s)
        if int(current_time) % 30 == 0:
            try:
                devices = get_bluetooth_devices()
                new_devices = set(devices) - set(state["last_bluetooth"])
                for device in new_devices:
                    add_event("bluetooth", f"{device} connected")
                state["last_bluetooth"] = devices
            except:
                pass
        
        # Monitor battery (every 5 mins)
        if int(current_time) % 300 == 0:
            try:
                battery = get_battery_level()
                if battery and battery <= 20 and current_time - state["last_battery_alert"] > 3600:
                    send_to_poke(f"This is an automated message being sent to you from Mac through your Poke API: ⚠️ Battery at {battery}% - Asif's laptop running low")
                    state["last_battery_alert"] = current_time
            except:
                pass
        
        # Posture reminder (every 50 mins of active time)
        if current_time - state["active_start_time"] > 3000 and current_time - state["last_posture_alert"] > 3600:
            send_to_poke("This is an automated message being sent to you from Mac through your Poke API: 💺 Posture Check - Asif has been working for 50+ minutes continuously")
            state["last_posture_alert"] = current_time
            state["active_start_time"] = current_time
        
        # Monitor meeting (every 20s)
        if int(current_time) % 20 == 0:
            try:
                meeting = get_meeting_process()
                if meeting and not state["meeting_process"]:
                    # Meeting started
                    add_event("meeting", f"Meeting started ({meeting})")
                    state["meeting_process"] = meeting
                    state["meeting_start"] = current_time
                elif not meeting and state["meeting_process"]:
                    # Meeting ended
                    duration = int((current_time - state["meeting_start"]) / 60)
                    add_event("meeting", f"Meeting ended ({state['meeting_process']}) - {duration} mins")
                    state["meeting_process"] = None
                    state["meeting_start"] = None
            except:
                pass
        
        # Save state
        save_state(state)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

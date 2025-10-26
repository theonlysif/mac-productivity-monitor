# 🖥️ Mac Productivity Monitor

Automated productivity tracking system for macOS that monitors your activity and sends updates to [Poke](https://poke.com) (or any messaging service).

Built to help AI assistants understand your work patterns and provide better productivity insights.

## ✨ Features

- **Sleep/Wake Tracking** - Get notified when laptop opens/closes
- **App & Window Monitoring** - Track which apps you use and what you're working on
- **Focus Mode Detection** - Know when Do Not Disturb is enabled
- **Location Tracking** - Based on WiFi network changes
- **Bluetooth Device Tracking** - Monitor AirPods and other device connections
- **Battery Alerts** - Get warnings at 20% and 10%
- **Posture Reminders** - Alerts after 50 minutes of continuous work
- **Meeting Duration Tracking** - Detect Zoom/Meet/Teams/Webex sessions

### Smart Batching
- Events are batched every 30 minutes (configurable)
- No spam - intelligent deduplication
- Immediate alerts for battery and posture (rate-limited to once per hour)

## 📋 Requirements

- macOS (tested on macOS Sonoma+)
- Python 3.7+
- Homebrew
- A [Poke](https://poke.com) account with API key

## 🚀 Installation

### 1. Install Dependencies

```bash
# Install SleepWatcher via Homebrew
brew install sleepwatcher

# Install Python requests library
pip3 install requests
```

### 2. Clone & Setup

```bash
git clone https://github.com/yourusername/mac-productivity-monitor.git
cd mac-productivity-monitor

# Make scripts executable
chmod +x install.sh
./install.sh
```

### 3. Configure Your API Key

Edit `productivity-monitor.py` and update:

```python
POKE_API_KEY = "your-poke-api-key-here"
```

Get your API key at: https://poke.com/settings/advanced

### 4. Start Services

```bash
# Start sleep/wake monitoring
brew services start sleepwatcher

# Start productivity monitoring
launchctl load ~/Library/LaunchAgents/com.user.productivity.plist
```

## 📁 File Structure

```
.
├── productivity-monitor.py          # Main monitoring script
├── sleep.sh                         # Sleep hook script
├── wakeup.sh                        # Wake hook script
├── com.user.productivity.plist      # LaunchAgent config
└── install.sh                       # Installation script
```

## 🎛️ Configuration

### Change Batch Interval

Edit `productivity-monitor.py`:

```python
BATCH_INTERVAL = 1800  # 30 minutes (in seconds)
```

### Ignore Additional Apps

Add to `IGNORED_APPS` set in `productivity-monitor.py`:

```python
IGNORED_APPS = {
    "Finder", "System Settings", ...,
    "YourAppName"
}
```

### Adjust Posture Reminder Time

```python
# Line 273 - currently 3000 seconds (50 mins)
if current_time - state["active_start_time"] > 3000:
```

## 🔧 Management Commands

```bash
# Stop productivity monitoring
launchctl unload ~/Library/LaunchAgents/com.user.productivity.plist

# Start productivity monitoring
launchctl load ~/Library/LaunchAgents/com.user.productivity.plist

# Check if running
launchctl list | grep productivity

# View logs
tail -f /tmp/productivity.log
tail -f /tmp/productivity.err

# Stop sleep/wake monitoring
brew services stop sleepwatcher

# Start sleep/wake monitoring
brew services start sleepwatcher
```

## 📤 Message Format

### Activity Updates (every 30 mins)
```
This is an automated message being sent to you from Mac through your Poke API
📊 Activity Update (10:00-10:30):
• 10:05 - Switched to VS Code
• 10:07 - Working on: project.py
• 10:15 - Focus Mode enabled
• 10:20 - Connected to: Home-WiFi
• 10:25 - AirPods connected
• 10:28 - Meeting started (Zoom)
```

### Immediate Alerts
```
This is an automated message being sent to you from Mac through your Poke API: ⚠️ Battery at 15% - Asif's laptop running low
```

## 🔌 Using Without Poke

To use with iMessage or other services, modify the `send_to_poke()` function in `productivity-monitor.py`:

### iMessage Example
```python
def send_to_poke(message):
    """Send via iMessage"""
    recipient = "+1234567890"
    script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{recipient}" of targetService
        send "{message}" to targetBuddy
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
```

### Slack Webhook Example
```python
def send_to_poke(message):
    """Send to Slack"""
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    requests.post(webhook_url, json={"text": message})
```

## 🛡️ Privacy & Security

- All data is stored locally in `/tmp/` directory
- No data is sent anywhere except your configured endpoint
- API keys are stored in plain text - keep `productivity-monitor.py` secure
- Consider using environment variables for API keys in production

## 🐛 Troubleshooting

### Monitor not starting
```bash
# Check LaunchAgent status
launchctl list | grep productivity

# Check for errors
cat /tmp/productivity.err
```

### No messages being sent
```bash
# Test API connection
curl 'https://poke.com/api/v1/inbound-sms/webhook' \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"message": "Test message"}'
```

### Permission issues
Go to System Settings → Privacy & Security → Accessibility and ensure Terminal/Python has permissions.

## 🤝 Contributing

Pull requests welcome! Please open an issue first to discuss changes.

## 📜 License

MIT License - feel free to modify and use for personal or commercial projects.

## 🙏 Credits

Built with love by [@theonlysif](https://twitter.com/theonlysif) | [onlysif.com](https://onlysif.com)

Powered by [Poke](https://poke.com) - AI personal assistant via text

---

**Note:** This monitors significant system activity. Use responsibly and be aware of privacy implications when sharing data with external services.

#!/bin/bash

set -e

echo "🖥️  Mac Productivity Monitor - Installation"
echo "==========================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install it first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Install SleepWatcher if not already installed
if ! brew list sleepwatcher &> /dev/null; then
    echo "📦 Installing SleepWatcher..."
    brew install sleepwatcher
else
    echo "✅ SleepWatcher already installed"
fi

# Install Python requests library
echo "📦 Installing Python requests library..."
pip3 install requests --quiet

echo ""
echo "🔧 Setting up scripts..."

# Prompt for API key
read -p "Enter your Poke API key (or press Enter to skip): " api_key

if [ -n "$api_key" ]; then
    # Update API key in productivity-monitor.py
    sed -i.bak "s/YOUR_POKE_API_KEY/$api_key/g" productivity-monitor.py
    sed -i.bak "s/pk_WIFHLZDJkWplNDhRDfles-en5a9w2U1ZNHHeuY-y-ig/$api_key/g" productivity-monitor.py
    
    # Update API key in sleep/wake scripts
    sed -i.bak "s/YOUR_POKE_API_KEY/$api_key/g" sleep.sh
    sed -i.bak "s/YOUR_POKE_API_KEY/$api_key/g" wakeup.sh
    
    # Remove backup files
    rm -f productivity-monitor.py.bak sleep.sh.bak wakeup.sh.bak
    
    echo "✅ API key configured"
else
    echo "⚠️  Skipped API key configuration. You'll need to manually edit:"
    echo "   - productivity-monitor.py (line 11)"
    echo "   - sleep.sh (line 3)"
    echo "   - wakeup.sh (line 3)"
fi

# Copy scripts to home directory
echo "📝 Installing scripts..."
cp productivity-monitor.py ~/productivity-monitor.py
chmod +x ~/productivity-monitor.py

cp sleep.sh ~/.sleep
chmod +x ~/.sleep

cp wakeup.sh ~/.wakeup
chmod +x ~/.wakeup

# Update LaunchAgent plist with actual username
username=$(whoami)
sed "s/asifhassan/$username/g" com.user.productivity.plist > ~/Library/LaunchAgents/com.user.productivity.plist

echo "✅ Scripts installed to home directory"
echo ""

# Prompt to start services
read -p "Start services now? (y/n): " start_services

if [ "$start_services" = "y" ]; then
    echo "🚀 Starting services..."
    
    # Start SleepWatcher
    brew services start sleepwatcher
    
    # Load productivity monitor
    launchctl load ~/Library/LaunchAgents/com.user.productivity.plist
    
    echo "✅ Services started!"
else
    echo "ℹ️  To start services later, run:"
    echo "   brew services start sleepwatcher"
    echo "   launchctl load ~/Library/LaunchAgents/com.user.productivity.plist"
fi

echo ""
echo "✨ Installation complete!"
echo ""
echo "📋 Useful commands:"
echo "   Stop monitoring:  launchctl unload ~/Library/LaunchAgents/com.user.productivity.plist"
echo "   Start monitoring: launchctl load ~/Library/LaunchAgents/com.user.productivity.plist"
echo "   View logs:        tail -f /tmp/productivity.log"
echo ""
echo "📖 Read the README.md for more configuration options!"

#!/bin/bash
# Stops the automatic export. Leaves your Desktop folders and clips untouched.
PLIST="$HOME/Library/LaunchAgents/com.theimancut.autoexport.plist"
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null; rm -f "$PLIST"; echo "Auto-export stopped. Folders were not touched."

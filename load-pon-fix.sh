#!/bin/sh
# Load PON poweroff overlay
# This adds system-power-controller to the PM8150B PON node

DTO=/pon-poweroff.dtbo
CONFIG=/sys/kernel/config/device-tree/overlays/pon-fix

if [ ! -f "$DTO" ]; then
    echo "DTBO not found: $DTO"
    exit 1
fi

# Check if already applied
if [ -d "$CONFIG" ]; then
    echo "PON fix overlay already loaded"
    exit 0
fi

mkdir -p "$CONFIG" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Failed to create configfs directory. Is configfs mounted?"
    mount -t configfs none /sys/kernel/config 2>/dev/null
    mkdir -p "$CONFIG"
fi

cat "$DTO" > "$CONFIG/dtbo" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "PON fix overlay loaded successfully"
    echo "Power off should now work correctly"
else
    echo "Failed to load overlay"
fi

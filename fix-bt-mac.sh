#!/bin/sh
# Generate BT MAC from machine-id and set it
MACHINE_ID=$(cat /etc/machine-id)
BT_MAC=$(echo -n "$MACHINE_ID" | sha256sum | sed 's/^\(..\)\(..\)\(..\)\(..\)\(..\).*$/02:\1:\2:\3:\4:\5/')
echo "Setting BT MAC to: $BT_MAC"

# Try btmgmt first, fallback to hcitool
if command -v btmgmt >/dev/null 2>&1; then
    btmgmt public-addr "$BT_MAC" 2>/dev/null
fi

# Bring up the adapter
hciconfig hci0 up 2>&1
hciconfig hci0 2>&1 | head -5

# Create systemd service for boot
cat > /etc/systemd/system/fix-bt-mac.service << SVCEOF
[Unit]
Description=Fix Bluetooth MAC address
After=bluetooth.service
Before=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fix-bt-mac.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable fix-bt-mac.service
echo "Service enabled for boot"

#!/bin/bash
set -e
DEBIAN_RAW=/tmp/debian_raw.img
RAMDISK_FW=/mnt/f/opencodeprojects/k30pro/temp_ramdisk_arch/usr/lib/firmware

# WiFi firmware
echo "Extracting WiFi firmware..."
mkdir -p "$RAMDISK_FW/ath11k/QCA6390/hw2.0/"
debugfs -R "dump /lib/firmware/ath11k/QCA6390/hw2.0/amss.bin /tmp/amss.bin" "$DEBIAN_RAW"
cp /tmp/amss.bin "$RAMDISK_FW/ath11k/QCA6390/hw2.0/amss.bin"

debugfs -R "dump /lib/firmware/ath11k/QCA6390/hw2.0/board-2.bin /tmp/board-2.bin" "$DEBIAN_RAW"
cp /tmp/board-2.bin "$RAMDISK_FW/ath11k/QCA6390/hw2.0/board-2.bin"

debugfs -R "dump /lib/firmware/ath11k/QCA6390/hw2.0/m3.bin /tmp/m3.bin" "$DEBIAN_RAW"
cp /tmp/m3.bin "$RAMDISK_FW/ath11k/QCA6390/hw2.0/m3.bin"

echo "WiFi firmware in ramdisk:"
ls -lh "$RAMDISK_FW/ath11k/QCA6390/hw2.0/"

# ADSP firmware
echo "Extracting ADSP firmware..."
mkdir -p "$RAMDISK_FW/qcom/sm8250/xiaomi/lmi/"
debugfs -R "dump /lib/firmware/qcom/sm8250/adsp.mbn /tmp/adsp.mbn" "$DEBIAN_RAW"
cp /tmp/adsp.mbn "$RAMDISK_FW/qcom/sm8250/xiaomi/lmi/adsp.mbn"

echo "ADSP firmware in ramdisk:"
ls -lh "$RAMDISK_FW/qcom/sm8250/xiaomi/lmi/"

echo "Done"

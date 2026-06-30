# AGENTS.md — Redmi K30 Pro (lmi) Mainline Linux

Goal: run mainline Linux on Redmi K30 Pro (SM8250) with WiFi / ADSP / GPU / Audio / Battery.

## Environment

- **Host**: Windows + WSL2 Ubuntu-22.04 + Docker (lmi-builder container)
- **Phone access**: ACM serial gadget → Putty + SSH (WiFi)
- **Base firmware**: MIUI 12.5 (TZ/SCM version tied to firmware signature)
- `fastboot` from Windows host
- **GitHub**: https://github.com/Zhuchen00123/lml_test

## Kernel

| Kernel | Version | Source | Status |
|--------|---------|--------|--------|
| **yuweiyuan8** | 6.19.0-rc8-sm8250+ | [yuweiyuan8/linux](https://github.com/yuweiyuan8/linux) v6.19 | **当前使用** (postmarketOS 官方 lmi 主线内核) |
| charisk | 6.19-rc8 | 从 boot_lmi.img 提取 | 备用 |
| ccc007ccc | 7.1.0 | /tmp/linux-sm8250-xiaomi-lmi (WSL) | 备用 |

**当前推荐**: yuweiyuan8 v6.19 + Debian 13 rootfs。已打包为 `boot-pmos-v3.img` (74MB)。

## 已修复的问题

### 蓝牙 BD 地址 (QCA6390) ✅
- **问题**: QCA6390 蓝牙驱动默认 MAC 是硬编码的 `00:00:00:00:5A:AD`，内核拒绝
- **修复**: 从 `/etc/machine-id` 生成真实 MAC 地址
- **脚本**: `fix-bt-mac.sh` (已推到 GitHub)
- **开机自启**: `fix-bt-mac.service` systemd 服务
- **参考**: Armbian PR #6727 有相同解决方案

### 关机 (Poweroff) ✅
- **问题**: DTS 缺 `system-power-controller` + qcom-pon 驱动未实现 poweroff
- **修复**: DTS 加 `&pon { system-power-controller; }` + 补丁 qcom-pon.c 驱动
- **补丁**: `patch_pon.py` (已推到 GitHub)

### Venus 视频编解码 ✅
- **问题**: venus.mbn 固件缺失
- **修复**: 从 [yuweiyuan8/firmware-xiaomi-lmi](https://github.com/yuweiyuan8/firmware-xiaomi-lmi) 下载固件
- **状态**: 固件已安装到 `/lib/firmware/qcom/sm8250/xiaomi/lmi/`，re-probe 成功 (video14 解码器 + video15 编码器)

## 待修复的问题

### 音频 ❌
- **问题**: `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=m` (模块) 与 `CONFIG_PINCTRL_SM8250_LPASS_LPI=y` (内建) 加载顺序冲突
- **症状**: Soundwire 链路无法建立，无声卡
- **根因**: `make defconfig` 覆盖了 sm8250.config 的 `=y` 设置
- **修复**: 重建内核，正确合并 config

### 电池 ❌
- **问题**: `CONFIG_BATTERY_QCOM_FG` 未设置，燃油计驱动缺失
- **症状**: 无 battery 设备，无法读取电量
- **根因**: 同上，config 合并问题
- **修复**: 重建内核，正确合并 config

### 快充 ⚠️
- **问题**: SMB5 DTS 节点缺少 `qcom,fast-charging-*` 参数
- **症状**: 限制在 USB 默认 500mA
- **修复**: 改 DTS 补充充电参数

### NFC ❌
- **问题**: I2C bus 1 (980000) pinctrl 配置错误
- **症状**: `pin-28 (980000.i2c): error -EINVAL`，NFC 芯片 nxp,pn553 无法探测
- **修复**: DTS 修复 pinctrl

### 摄像头 ❌
- **问题**: OV13B10 sensor I2C 通信失败 (-EIO)
- **症状**: `ov13b10 21-0020: failed to find sensor: -5`
- **修复**: DTS 修复电源域

### 传感器 ❌
- **问题**: SLPI 固件缺失
- **症状**: 加速度计/陀螺仪/磁力计/环境光不可用
- **修复**: 固件已安装，待重启验证

## Config 合并问题 (核心问题)

**问题**: `make defconfig sm8250.config` 没有正确合并——defconfig 覆盖了 sm8250.config 的 `=y` 设置。

**yuweiyuan8 的 sm8250.config 期望**:
- `CONFIG_SND_SOC_QDSP6_PRM=y` (内建)
- `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=y` (内建)
- `CONFIG_BATTERY_QCOM_FG=y` (内建)

**实际运行内核**:
- `CONFIG_SND_SOC_QDSP6_PRM=m` (模块)
- `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=m` (模块)
- `CONFIG_BATTERY_QCOM_FG` 未设置

**修复方法**:
```bash
# 正确合并 config
make ARCH=arm64 defconfig
scripts/kconfig/merge_config.sh -m .config arch/arm64/configs/sm8250.config
# 强制设置关键选项
sed -i 's/CONFIG_SND_SOC_QDSP6_PRM=m/CONFIG_SND_SOC_QDSP6_PRM=y/' .config
sed -i 's/CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=m/CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=y/' .config
sed -i 's/# CONFIG_BATTERY_QCOM_FG is not set/CONFIG_BATTERY_QCOM_FG=y/' .config
# 编译
make -j8 ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image.gz modules dtbs
```

**注意**: `make olddefconfig` 会覆盖手动修改，必须在编译前直接编辑 .config。

## Firmware

### 固件路径 (DTS 精确匹配)
- WiFi: `/lib/firmware/ath11k/QCA6390/hw2.0/` (amss.bin, board-2.bin, m3.bin)
- ADSP: `/lib/firmware/qcom/sm8250/xiaomi/lmi/adsp.mbn`
- CDSP: `/lib/firmware/qcom/sm8250/xiaomi/lmi/cdsp.mbn`
- SLPI: `/lib/firmware/qcom/sm8250/xiaomi/lmi/slpi.mbn`
- Venus: `/lib/firmware/qcom/sm8250/xiaomi/lmi/venus.mbn`
- GPU: `/lib/firmware/qcom/sm8250/xiaomi/lmi/a650_zap.mbn`

### 固件来源
- **[yuweiyuan8/firmware-xiaomi-lmi](https://github.com/yuweiyuan8/firmware-xiaomi-lmi)**: lmi 专属固件 (推荐)
- **MIUI 12.5 `NON-HLOS.bin`**: FAT16 镜像，需补零到 469MB 用 7-Zip 打开
- **linux-firmware 通用**: `/lib/firmware/` 标准路径

### 关键固件问题
- **ADSP**: lmi 原厂分片 `.mdt`+`.b00-.b18` 被 TZ 签名拒绝 (`error -22`)，需用 yuweiyuan8 的 `adsp.mbn`
- **WiFi 校准**: `board_id 0xff` 表示驱动读不到芯片 OTP 数据
- **WiFi amss**: lmi 原厂 `amss20.bin` (4.2MB) 需改名 `amss.bin`

## Rootfs (Debian 13)

### 当前配置
- 分区: `/dev/sda34` (464.5GB，已在线扩展)
- 内核 cmdline: `root=UUID=d7e36bed-3d3f-451b-8d0c-197a356a5ac0 systemd.gpt_auto=0`
- 用户: `root` / 密码: `root123`, hostname: `lmi`
- WiFi 接口: `wlp1s0` (NetworkManager 管理)
- 桌面: Phosh (GNOME 移动版)
- 时区: Asia/Shanghai

### 已安装服务
- `fix-bt-mac.service`: 蓝牙 MAC 地址修复
- `NetworkManager`: WiFi 管理
- `ssh.service`: SSH 服务
- `phosh.service`: Phosh 桌面

## 刷机命令

```bash
# 从 Windows host:
fastboot flash boot boot-pmos-v3.img    # 永久刷入 yuweiyuan8 内核
fastboot reboot

# 串口检查:
dmesg | grep -iE 'venus|cdsp|slpi|adsp|sensor|battery|audio' | head -20

# WiFi 状态:
nmcli device status
nmcli device wifi list

# 蓝牙状态:
bluetoothctl power on
bluetoothctl scan on
```

## 文件布局

```
F:\opencodeprojects\k30pro\
├── boot-pmos-v3.img           # yuweiyuan8 v6.19 + 固件 + Debian rootfs (74MB)
├── boot-pmos-v4.img           # v4 (固件加入 ramdisk，待测试)
├── boot-charisk-debian.img    # charisk 内核 (备用)
├── boot_lmi.img               # Arch charisk 6.19-rc8 (仅参考)
├── rootfs_lmi.img.simg        # Arch rootfs (仅参考)
├── fix-bt-mac.sh              # 蓝牙 MAC 修复脚本
├── fix_dts.py                 # DTS 补丁 (system-power-controller)
├── patch_pon.py               # qcom-pon.c 补丁 (poweroff)
├── fw-lmi.tar.gz              # yuweiyuan8 固件包 (17MB)
├── AGENTS.md                  # 本文件
├── update.md                  # 迭代记录
├── img.md                     # img 文件说明
├── 备份/
│   ├── stock-boot.img         # MIUI 12.5 原厂 boot (128MB)
│   ├── boot-lmi-hybrid.img    # ccc 7.1.0, 无固件 (36.6MB)
│   ├── boot-wifi.img          # ccc 7.1.0, 全固件 ramdisk (80MB)
│   ├── rootfs_lmi_acm.img     # Debian 13 rootfs (3014.2MB)
│   └── boot-charisk-debian.img  # charisk 6.19 + 模块 + Debian (35.4MB)

C:\Users\15185\Desktop\mi12\images\  # MIUI 12.5 线刷包 (固件源)
Docker: lmi-builder container          # 内核编译环境
GitHub: Zhuchen00123/lml_test          # 项目仓库
```

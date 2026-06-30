# AGENTS.md — Redmi K30 Pro (lmi) Mainline Linux

Goal: run mainline Linux on Redmi K30 Pro (SM8250) with WiFi / ADSP / GPU.

## Environment

- **Host**: Windows + WSL2 Ubuntu-22.04 (kernel → no `metadata_csum` support)
- **Phone access**: ACM serial gadget → Putty only. No USB keyboard, no OTG, no display.
- **Base firmware**: MIUI 12.5 (TZ/SCM version tied to firmware signature)
- `fastboot` from Windows host

## Kernel

Two kernel approaches:

| Kernel | Version | WiFi strategy | Source |
|--------|---------|---------------|--------|
| **yuweiyuan8** | 6.19.0-rc8-sm8250+ | ATH11K=m | [yuweiyuan8/linux](https://github.com/yuweiyuan8/linux) v6.19 (postmarketOS 官方 lmi 主线内核) |
| charisk | 6.19-rc8 | ATH11K=m, 模块在 ramdisk | 从 boot_lmi.img 提取 kernel + 从 rootfs_lmi.img.simg 提取模块 |
| ccc007ccc | 7.1.0 | ATH11K=y (全部内建) | /tmp/linux-sm8250-xiaomi-lmi (WSL) |

**当前推荐**: yuweiyuan8 v6.19 + Debian 13 rootfs。已打包为 `boot-pmos-v3.img` (74MB)。

## 已修复的问题

### 蓝牙 BD 地址 (QCA6390)
- **问题**: QCA6390 蓝牙驱动默认 MAC 是硬编码的 `00:00:00:00:5A:AD`，内核拒绝
- **修复**: 从 `/etc/machine-id` 生成真实 MAC 地址
- **脚本**: `fix-bt-mac.sh` (已推到 GitHub)
- **开机自启**: `fix-bt-mac.service` systemd 服务

### 关机 (Poweroff)
- **问题**: DTS 缺 `system-power-controller` + qcom-pon 驱动未实现 poweroff
- **修复**: DTS 加 `&pon { system-power-controller; }` + 补丁 qcom-pon.c 驱动

### 音频 (待修复)
- **问题**: `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=m` (模块) 与 `CONFIG_PINCTRL_SM8250_LPASS_LPI=y` (内建) 加载顺序冲突
- **修复**: 重建内核，改 config `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=y`

**当前推荐**: 用 charisk 内核 + 模块扩展 ramdisk + Debian rootfs。已打包为 `boot-charisk-debian.img` (42.9MB)。

**注意 — charisk DTS 路径差异**:
- ADSP: `qcom/sm8250/xiaomi/lmi/adsp.mbn` (比 ccc 多一层 `xiaomi/lmi/`)
- GPU zap: `a650_zap.mbn` (ccc 用 `a650_zap.mdt`)

**关键教训 — ATH11K 加载方式**:
- `CONFIG_ATH11K=y` → 开机 2.8s 初始化，PCIe 链路未就绪 → `soc_id 0xffffffff` / `MHI_CB_EE_RDDM`
- `CONFIG_ATH11K=m` → 系统启动完后 module load，PCIe 正常
- 如果不重建内核，用 unbind/bind 模拟延迟加载:
  ```bash
  echo 0000:01:00.0 > /sys/bus/pci/drivers/ath11k_pci/unbind
  sleep 2
  echo 0000:01:00.0 > /sys/bus/pci/drivers/ath11k_pci/bind
  ```

**不要做的事**:
- 不要用 `make defconfig` 重建内核 — defconfig 缺少关键平台驱动，系统切根失败
- 要改动 =y/=m 时在原 `.config` 上直接 edit，不要重新生成

## Firmware

### 固件路径 (DTS 精确匹配)
- WiFi: `/lib/firmware/ath11k/QCA6390/hw2.0/` (内核查 `ath11k/QCA6390/hw2.0/amss.bin`)
- ADSP: `/lib/firmware/qcom/sm8250/adsp.mbn` (DTS 写死 `.mbn`，不是 `.mdt`)
- GPU: `/lib/firmware/qcom/sm8250/adreno/` (a650_zap.mdt/a650_sqe.fw/a650_gmu.bin)
- Venus: `/lib/firmware/qcom/sm8250/venus/` (venus.mbn + .b00-.b10,b19)

### 固件来源
- **MIUI 12.5 `NON-HLOS.bin`**: FAT16 镜像，**必须先补零到 469MB** 才能用 7-Zip 打开
  - 路径: `C:\Users\15185\Desktop\mi12\images\NON-HLOS.bin`
  - 包含: `image/adsp.*`, `image/venus.*`, `image/qca6390/*`
- **linux-firmware 通用**: `/lib/firmware/` 标准路径
  - `adsp.mbn` (15MB 通用版) → 替代 lmi 分片固件
  - `board-2.bin` (7MB, 不含 lmi 校准)
- **`dspso.bin`**: ext4 分区仅含 `.so` 运行时库，无 `.mbn` 固件 — 不用

### DTS firmware-name 匹配
内核 `request_firmware()` 精确匹配扩展名。DTS 写 `adsp.mbn` 就必须叫 `adsp.mbn`，不能用 `adsp.mdt`。同理 `venus.mbn`、`a650_zap.mdt`（注意 GPU zap 用 `.mdt`）。

### 关键固件问题
- **ADSP**: lmi 原厂分片 `.mdt`+`.b00-.b18` 被 TZ 签名拒绝 (`error -22`)，需用 linux-firmware 通用 15MB `adsp.mbn`
- **WiFi 校准**: `board_id 0xff` 表示驱动读不到芯片 OTP 数据。`bdwlan` 原始文件需专有转换工具才能用，linux-firmware `board-2.bin` 不含 K30 Pro 校准条目
- **WiFi amss**: lmi 原厂 `amss20.bin` (4.2MB) 需改名 `amss.bin`，解决 MHI 超时

## Rootfs (Debian 13)

### 构建流程
1. Docker+QEMU debootstrap → 生成 tarball
2. `mke2fs -d` 写入 ext4 镜像
3. `img2simg` 转 sparse image 供 fastboot 刷入
4. WiFi/SSH/串口配置用 `debugfs -w` 注入

### 关键配置
- 内核 cmdline: `root=UUID=d7e36bed-3d3f-451b-8d0c-197a356a5ac0 systemd.gpt_auto=0`
- 用户: `root` / 密码: `root123`, hostname: `lmi`
- 镜像源: USTC
- WiFi 接口: `wlp1s0` (可预测命名，不是 `wlan0`)
- ACM 串口 gadget: `/opt/gadget.sh` + systemd 服务

## 刷机命令

```bash
# 从 Windows host:
fastboot boot boot-charisk-debian.img                                            # RAM only charisk+Debian (推荐)
fastboot boot boot-wifi.img                                           # RAM only ccc 内核
fastboot flash boot boot-wifi.img                                     # 永久刷入
fastboot flash userdata debian-full.simg                              # 刷 rootfs

# ADSP 状态检查:
dmesg | grep -i adsp
dmesg | grep -i "error -22\|qcom_q6v5"

# WiFi 状态检查:
dmesg | grep ath11k | tail -5
ip link show

# 手动加载 ATH11K 模块 (charisk 内核自动加载，仅 ccc 内核需此操作):
modprobe ath11k_pci
```

## 文件布局

```
F:\opencodeprojects\k30pro\
├── boot_lmi.img              # Arch charisk 6.19-rc8 (WiFi 可用，仅参考)
├── rootfs_lmi.img.simg       # Arch rootfs (仅参考)
├── boot-charisk-debian.img   # charisk 内核 + 模块扩展 ramdisk + Debian rootfs (35.4MB)
├── img.md                    # 各 img 文件详细迭代说明
├── update.md                 # 每次迭代记录 (变更+测试结果)
├── AGENTS.md                 # 本文件
├── 备份/
│   ├── stock-boot.img        # MIUI 12.5 原厂 boot (128MB)
│   ├── boot-lmi-hybrid.img   # ccc 7.1.0, 无固件 (36.6MB)
│   ├── boot-wifi.img         # ccc 7.1.0, 全固件 ramdisk (80MB)
│   ├── rootfs_lmi_acm.img    # Debian 13 rootfs (3014.2MB)
│   └── boot-charisk-debian.img  # charisk 6.19 + 模块 + Debian (35.4MB)

C:\Users\15185\Desktop\mi12\images\  # MIUI 12.5 线刷包 (固件源)
C:\Users\15185\AppData\Local\Temp\opencode\  # 构建脚本
/tmp/linux-sm8250-xiaomi-lmi (WSL)  # 内核源码
```

# Image File Reference — lmi (Redmi K30 Pro)

## Root directory — 最初 Arch 版本 (不可动)

### `boot_lmi.img` (26.7MB)
- **内核**: charisk 6.19-rc8 mainline
- **WiFi**: 可用 (ATH11K=m 模块方式，系统启动完才加载)
- **ADSP/GPU**: 不明 (未详细测试)
- **用途**: 最初能跑 WiFi 的 Arch 基线，仅做参考

### `rootfs_lmi.img.simg` (3014.2MB)
- **内容**: Arch Linux ARM rootfs (sparse image)
- **配对内核**: boot_lmi.img
- **WiFi**: 可用 (配 charisk 内核)
- **用途**: Arch 基线 rootfs，仅做参考

### `boot-charisk-debian.img` (42.9MB)
- **内核**: charisk 6.19.0-rc8-lmi+ (从 boot_lmi.img 提取)
- **Ramdisk**: Arch mkinitcpio ramdisk + 788 个 6.19.0-rc8-lmi+ 内核模块 + WiFi 固件 + ADSP 固件
  - WiFi: amss.bin (3.5MB), board-2.bin (227KB), m3.bin (261KB) at `ath11k/QCA6390/hw2.0/`
  - ADSP: adsp.mbn (15MB) at `qcom/sm8250/xiaomi/lmi/` (charisk DTS 路径)
  - GPU: a650_zap.mbn, a650_sqe.fw, a650_gmu.bin
- **Rootfs**: Debian 13 (UUID 挂载，同 boot_lmi.img)
- **WiFi**: 预期可用 — ATH11K=m 模块+固件均在 ramdisk
- **迭代**: v5 — 注入 michael_mic 预加载配置，解决 WPA 连接所需 crypto 算法
- **闪存命令**: `fastboot boot boot-charisk-debian.img`

---

## `备份/` — 迭代构建版本

### `stock-boot.img` (128MB)
- **来源**: MIUI 12.5 原厂 boot
- **内容**: 原厂内核 + ramdisk
- **用途**: 紧急恢复/原厂基线

### `boot-lmi-hybrid.img` (36.6MB)
- **内核**: ccc007ccc 7.1.0，全部驱动 =y 内建，ramdisk 无固件
- **Rootfs**: Debian 13 (UUID 挂载)
- **WiFi**: 不可用 — ATH11K=y 在启动 2.8s 初始化，PCIe 未就绪 (`soc_id 0xffffffff`)
- **ADSP**: 不可用 — ramdisk 无 ADSP 固件
- **迭代**: 第一个 Debian boot，仅验证基本启动流程

### `boot-wifi.img` (80MB)
- **内核**: ccc007ccc 7.1.0，全部驱动 =y，ramdisk 含全部 39 个固件
- **Rootfs**: Debian 13 (UUID 挂载)
- **WiFi**: 半可用 — ath11k MHI 通、固件加载成功，但 PCIe 初始化早导致 `soc_id 0xffffffff` / 固件崩溃 (`MHI_CB_EE_RDDM`)
  - 修复方向: `echo 0000:01:00.0 > /sys/bus/pci/drivers/ath11k_pci/unbind; sleep 2; echo 0000:01:00.0 > /sys/bus/pci/drivers/ath11k_pci/bind`
  - 板级校准: 缺 lmi 专用 board-2.bin (`board_id 0xff` 读不到芯片 OTP)
- **GPU**: 正常 — `a650_zap.mdt`, `a650_sqe.fw`, `a650_gmu.bin`，`Loaded GMU firmware v2.1.8`
- **ADSP**: 待验证 — 使用 linux-firmware 通用 15MB `adsp.mbn` (lmi 分片固件被 TZ 拒绝 `-22`)
- **Venus**: 已注入 lmi 原厂 `.mbn` + `.b00-.b10,b19`
- **固件来源**: MIUI 12.5 `NON-HLOS.bin` (FAT16，需补零到 469MB)
- **迭代**: 注入全部固件到 ramdisk，解决内建驱动早期加载需求

### `rootfs_lmi_acm.img` (3014.2MB)
- **内容**: Debian 13 rootfs (sparse image)，ACM 串口 gadget + WiFi 配置
- **预装**: e2fsprogs, wpasupplicant, openssh-server, sudo, chrony, ca-certificates
- **配置**: USTC 镜像源，WiFi 预配置，hostname=lmi，root/root123
- **迭代**: 首次 Debian rootfs，基础可用

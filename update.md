# 迭代记录 — lmi (Redmi K30 Pro)

---

## 迭代 1: 首次 Debian boot → ccc 内核无固件

**日期**: 2026-05 (估算)  
**Boot 文件**: `备份/boot-lmi-hybrid.img` (36.6MB)

### 变更内容
- 内核: ccc007ccc 7.1.0，全部驱动内建 (=y)
- Ramdisk: 最小化，无固件文件
- Rootfs: Debian 13，Docker+QEMU debootstrap 构建
- Cmdline: `root=UUID=d7e36bed-3d3f-451b-8d0c-197a356a5ac0 systemd.gpt_auto=0`

### 测试结果
| 项目 | 状态 | 说明 |
|------|------|------|
| 基本启动 | ✅ | Debian 正常进入 |
| ATH11K/WiFi | ❌ | ATH11K=y 在 2.8s 初始化，PCIe 未就绪 → `soc_id 0xffffffff` |
| ADSP | ❌ | 无固件文件 |
| GPU | ❌ | 无固件文件 |

### 问题
- defconfig 重建导致系统切根失败（缺关键平台驱动），已回滚
- 确认 ATH11K=y 导致初始化时序问题

---

## 迭代 2: 全固件注入 → ccc 内核 ramdisk

**日期**: 2026-05 ~ 2026-06  
**Boot 文件**: `备份/boot-wifi.img` (80MB)

### 变更内容
- 内核: ccc007ccc 7.1.0 (同迭代 1，未重建)
- Ramdisk: 注入全部 39 个固件文件到 `/usr/lib/firmware/`
  - **GPU**: `a650_zap.mdt` (14KB), `a650_sqe.fw` (32KB), `a650_gmu.bin` (42KB)
  - **ADSP**: lmi 原厂分片 `.mdt` + `.b00-.b18` (从 NON-HLOS.bin 提取)
  - **Venus**: lmi 原厂 `.mbn` + `.b00-.b10,b19`
  - **WiFi**: `amss20.bin`→`amss.bin` (4.2MB), `bdwlan.e01`→`board.bin` (57KB), `board-2.bin` (7MB), `m3.bin`, `regdb.bin`
- DTS firmware-name 匹配修复: `adsp.mdt`→`adsp.mbn`, `a650_zap.mbn`→`a650_zap.mdt`
- Rootfs: Debian 13 (同迭代 1)，预装 e2fsprogs, wpasupplicant, openssh-server, sudo, chrony, ca-certificates

### 测试结果
| 项目 | 状态 | 说明 |
|------|------|------|
| 基本启动 | ✅ | Debian 正常进入 |
| GPU | ✅ | `Loaded GMU firmware v2.1.8` |
| ATH11K/WiFi | ⚠️ 半可用 | MHI 通、固件加载成功，但时序问题导致 `soc_id 0xffffffff` / `MHI_CB_EE_RDDM` |
| WiFi 校准 | ❌ | `board_id 0xff`，缺 lmi 专用校准文件 |
| ADSP | ⚠️ 待验证 | lmi 分片被 TZ 拒绝 (-22)，已换用 linux-firmware 通用 15MB `adsp.mbn` |

### 修复方向
- `echo 0000:01:00.0 > /sys/bus/pci/drivers/ath11k_pci/unbind; sleep 2; echo 0000:01:00.0 > /sys/bus/pci/drivers/ath11k_pci/bind`
- 需找 lmi 专用 board-2.bin 或 bdwlan 转换工具

---

## 迭代 3: charisk 内核 + Debian rootfs → ATH11K=m 模块方式

**日期**: 2026-06-28  
**Boot 文件**: `boot-charisk-debian.img` / `备份/boot-charisk-debian.img` (35.4MB)

### 变更内容
- **内核**: charisk 6.19.0-rc8-lmi+ (从 `boot_lmi.img` 解包提取，gzip 压缩 12.3MB)
  - `CONFIG_ATH11K=m` — 系统启动完才加载模块
- **Ramdisk**: Arch mkinitcpio ramdisk (boot_lmi.img 原 ramdisk) + 扩展
  - GPU 固件 (a650_gmu.bin, a650_sqe.fw, a650_zap.mbn)
  - **788 个 6.19.0-rc8-lmi+ 内核模块** (从 `rootfs_lmi.img.simg` 提取，含 ath11k.ko / ath11k_pci.ko)
  - ramdisk 总压缩尺寸: 24.1MB
- **Rootfs**: Debian 13 (`备份/rootfs_lmi_acm.img`)，含 WiFi 固件
  - `/lib/firmware/ath11k/QCA6390/hw2.0/` — amss.bin, board-2.bin, m3.bin
  - 同 Arch 配方: 固件在 rootfs，模块在 ramdisk

### 关键设计决策
- cmdline 与 Arch `boot_lmi.img` 完全相同 — UUID 刚好匹配 Debian rootfs
- 不修改 Debian rootfs，WiFi 固件已存在于 rootfs 中
- DTB 依赖手机 dtbo 分区 (MIUI 12.5)，与 Arch 启动时相同

### 测试结果 (2026-06-28)
| 项目 | 状态 | 说明 |
|------|------|------|
| 基本启动 | ✅ | Debian 正常进入 |
| ATH11K/WiFi | ❌→⚠️ | 模块早于 rootfs 加载，amss.bin -2；wlan0 出来但 michael_mic 缺失 |
| ADSP | ❌ | 路径不匹配：`xiaomi/lmi/` 多一层子目录 |
| GPU | ✅ | `Loaded GMU firmware v2.1.8` |

### 发现
- modules-load.d 找不到模块：`Failed to find module 'ath11k_pci'` — systemd 在 rootfs `/lib/modules/` 找，但模块在 ramdisk
- ADSP firmware-name 多一层 `xiaomi/lmi/` 子目录

---

## 迭代 4: WiFi+ADSP 固件注入 ramdisk → charisk 内核

**日期**: 2026-06-28  
**Boot 文件**: `boot-charisk-debian.img` / `备份/boot-charisk-debian.img` (42.9MB)

### 变更内容
- **WiFi 固件注入 ramdisk** (`/usr/lib/firmware/ath11k/QCA6390/hw2.0/`)
  - amss.bin (3.5MB), board-2.bin (227KB), m3.bin (261KB)
  - 从 Debian rootfs 提取，解决模块早于 rootfs 加载的时序问题
- **ADSP 固件路径修正** (`/usr/lib/firmware/qcom/sm8250/xiaomi/lmi/`)
  - adsp.mbn (15MB) — charisk DTS 多一层 `xiaomi/lmi/`
- ramdisk 总压缩尺寸: 31MB (v1 24MB + 7MB 固件)

### 测试结果
| 项目 | 状态 | 说明 |
|------|------|------|
| 基本启动 | ✅ | Debian 正常进入 |
| ATH11K/WiFi | ⚠️ 半可用 | wlan0 接口出现、扫描到 AP，但建连接时 `michael_mic` 缺失 (-2) |
| ADSP | ❌ | 路径修正后加载，但通用 adsp.mbn 被 TZ 签名拒绝 (error -22) |
| GPU | ✅ | 不变 |

### 发现
- `michael_mic` crypto 算法模块不会被 ath11k 自动加载，需手动预加载
- modules-load.d 在 ramdisk 里执行太晚，ath11k 先在 3.5s 初始化

---

## 迭代 5: 预加载 michael_mic — modules-load.d

**日期**: 2026-06-28  
**Boot 文件**: `boot-charisk-debian.img` / `备份/boot-charisk-debian.img` (42.9MB)

### 变更内容
- 在 ramdisk 创建 `/usr/lib/modules-load.d/michael_mic.conf` 预加载 `michael_mic` crypto 模块
- 其余同迭代 4

### 测试结果
| 项目 | 状态 | 说明 |
|------|------|------|
| 基本启动 | ✅ | Debian 正常进入 |
| ATH11K/WiFi | ✅ | wlan0 认证关联成功、DHCP 获取 IP `10.186.188.236/24` |
| ADSP | ❌ 不变 | TZ 签名问题需 lmi 专用固件 |

### 刷机命令
```bash
fastboot boot C:\Users\Public\boot-charisk-debian.img
```

---

## 迭代 6: yuweiyuan8/kernel v6.19 主线内核 + Debian 13

**日期**: 2026-06-30  
**Boot 文件**: `boot-pmos-v3.img` (74MB)  
**内核**: [yuweiyuan8/linux](https://github.com/yuweiyuan8/linux) v6.19 (postmarketOS 官方 lmi 主线内核)

### 变更内容
- **内核**: yuweiyuan8/linux v6.19 stable，`defconfig + sm8250.config`，gcc 11.4 交叉编译
- **DTS**: `sm8250-xiaomi-lmi.dts` (1505行，postmarketOS 版本)
  - 新增 `&pm8150b_pon { status = "okay"; system-power-controller; }` → 后改为 `&pon { system-power-controller; }` (修正到 PM8150 而非 PM8150B)
- **qcom-pon.c 补丁**: 新增 `pm_power_off` 回调，写 `PON_PS_HOLD_RESET_CTL` 寄存器触发 PS_HOLD 关机
- **CONFIG_ARM64_APPENDED_DTB=y**：内核 Image.gz 末尾拼接 DTB
- **Ramdisk**: 复用 charisk Arch initramfs (systemd-based)，替换模块为 yuweiyuan8 版 (792个 .ko)
- **蓝牙固件**: `htbtfw20.tlv` + `htnv20.bin` + `hpnv20.bin` 从 linux-firmware 获取
- **Rootfs**: Debian 13 (`/dev/sda34` 464.5GB 分区，已在线扩展)

### 测试结果
| 项目 | 状态 | 说明 |
|------|------|------|
| 基本启动 | ✅ | Debian 正常进入，`uname -r: 6.19.0-rc8-sm8250+` |
| WiFi | ✅ | wlp1s0，IP 10.115.46.6，NetworkManager 管理 |
| GPU | ✅ | Adreno A650, `/dev/dri/card0` + `renderD128` |
| 关机 | ✅ | `poweroff` 正常关机（v3 修复 qcom-pon 驱动后） |
| 显示 | ✅ | DSI-1 1080x2400 |
| 触控 | ✅ | FT3518 多点触控 |
| 充电 | ⚠️ 500mA | SMB5 限制 500mA，DTS 缺 fast-charging 参数 |
| 音频 | ❌ | **LPASS pinctrl 找不到 'core' 时钟** — `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=m` (模块) 与 `CONFIG_PINCTRL_SM8250_LPASS_LPI=y` (内建) 加载顺序冲突 |
| 电池 | ❌ | qcom_battmgr 模块未加载，无 battery 设备 |
| 蓝牙 | ⚠️ | 固件加载成功 (`QCA setup on UART is completed`)，但 BD 地址 `00:00:00:00:5A:AD` (无效，缺少设备专属 NVM) |
| Phosh 桌面 | ✅ | 安装成功，有锁屏界面，输入密码可进桌面 |

### 音频问题详细分析
```
platform 33c0000.pinctrl: deferred probe pending: qcom-sm8250-lpass-lpi-pinctrl: Failed to get clk 'core'
platform 3200000.rxmacro: deferred probe pending: wait for supplier /soc@0/pinctrl@33c0000/rx-swr-active-state
platform 3220000.txmacro: deferred probe pending: wait for supplier /soc@0/pinctrl@33c0000/tx-swr-active-state
platform 3210000.soundwire: deferred probe pending: supplier 3200000.rxmacro not ready
platform 3230000.soundwire: deferred probe pending: supplier 3220000.txmacro not ready
platform 3370000.codec: deferred probe pending: va_macro: unable to get macro clock
```
**根因**: `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS` 编译为模块 (=m)，但 LPASS LPI pinctrl 是内建 (=y)。pinctrl 驱动开机就加载，需要 `core` 时钟，但时钟模块还没加载 → 永久 deferred probe → Soundwire 链路无法建立 → 无声卡。

**修复**: 重建内核，改 config `CONFIG_SND_SOC_QDSP6_PRM_LPASS_CLOCKS=y`。

### 蓝牙问题
BD 地址 `00:00:00:00:5A:AD` 是 QCA 默认值，缺少设备专属的蓝牙 NVM 校准文件。真实 MAC 地址在 MIUI persist 分区 (`/dev/sda22`) 或需要从 MIUI 原厂固件中提取 `htnv20.bin`。

### 充电问题
SMB5 DTS 节点缺少 `qcom,fast-charging-*` 参数，限制在 USB 默认 500mA。标准 PD 协商到 5V/3A 但驱动没用上。

### 贡献者
- yuweiyuan8/linux 内核源码 (postmarketOS 官方 lmi 主线)
- postmarketOS wiki: https://wiki.postmarketos.org/wiki/Xiaomi_POCO_F2_Pro_(xiaomi-lmi)

### 刷机命令
```powershell
fastboot flash boot F:\opencodeprojects\k30pro\boot-pmos-v3.img
fastboot reboot
```
> 注意：`fastboot boot` 对 74MB 镜像会 Load Error，必须用 `fastboot flash boot`。

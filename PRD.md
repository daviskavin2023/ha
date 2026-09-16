# 产品需求文档 (PRD) - 3038 网关 (Home Assistant 接管小米中枢)

| 项目名称 | 3038-网关-ha (Home Assistant 智能家居网关中心) |
| :--- | :--- |
| **版本** | v1.1.0 |
| **创建日期** | 2026-09-16 |
| **最后修订** | 2026-09-16 |
| **状态** | 待执行 / 规划定稿 (Ready for Execution) |
| **负责人** | Kavin |
| **PVE 宿主** | `10.10.10.10` (PVE 8.3.0) |
| **虚拟机目标** | KVM HAOS (VMID `138`, IP `10.10.10.38/24`, 网关/DNS `10.10.10.15`) |
| **外网域名** | `https://ha.808608.xyz` (Cloudflare Tunnel: `808608`) |
| **核心定位** | **逻辑控制中心全面替代小米中枢任务编排；小米中枢仅保留作为射频接收器 (BLE Mesh / Zigbee 基站)** |

---

## 1. 项目背景与痛点分析

### 1.1 现状与架构痛点
* **现有方案**：全屋智能开关、计量插座挂载于小米中枢网关及米家生态下，由米家 App / 中枢极客版负责自动化任务编排。
* **核心痛点**：
  1. **自动化表达能力匮乏**：米家仅支持基础的 `IF-THEN` 线性模型，缺乏持续时长（`for: xx`）、防抖、多条件与/或逻辑、以及基于状态机的复杂逻辑。
  2. **规则碎片化与冗余**：多键开关的单击、双击、长按在米家中需拆分为多条独立规则，导致全屋规则数量膨胀且极难协同排查。
  3. **生态封闭孤岛**：无法联动 PVE 宿主机状态、软路由网络在线状态（10.10.10.15）、NAS 备份状态、飞书 Webhook 告警或跨品牌传感器。
  4. **大功率插座判定痛点**：米家无法稳定支持“功率降至 5W 且**持续保持 5 分钟**后断电”，家电待机微小波动极易引发误断电。

### 1.2 改造目标与核心决策
* **决策：采用方案 A（逻辑控制替代，物理硬件共存）**：
  * **主控大脑**：在 PVE 10 宿主机上部署标准 **Home Assistant Operating System (HAOS)**，承担全屋设备状态总线、高阶任务编排、能源统计看板与 Apple HomeKit / Siri 桥接。
  * **信号基站**：保留现存小米中枢网关（以及多模网关），**仅作为底层射频天线（Bluetooth Mesh / Zigbee 基站）**，为物理开关插座提供无线中继，不运行任何上层自动化。
  * **通信模式**：HA 通过 `Xiaomi Miot Auto` 插件在局域网内与设备/中枢通信（Local Token LAN RPC），实现毫秒级响应，即使宽带断网亦完全正常运转。

---

## 2. 系统拓扑与网络端口架构

### 2.1 整体网络与控制流拓扑
```text
┌────────────────────────────────────────────────────────────────────────┐
│                        公网客户端 (Siri / App / 浏览器)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS (TLS 443)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Cloudflare Edge & Tunnel                         │
│                    外网域名: https://ha.808608.xyz                      │
│                    隧道接入点: Tunnel ID 808608                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 安全内网隧道穿透
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          家庭局域网 (10.10.10.0/24)                     │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                      上游主路由 (10.10.10.1)                     │   │
│   │                     (DHCP 静态租约 / 物理交换)                   │   │
│   └───────────────┬────────────────────────────────┬───────────────┘   │
│                   │                                │                   │
│   ┌───────────────▼────────────────┐   ┌───────────▼───────────────┐   │
│   │       旁路由 (10.10.10.15)      │   │     PVE 宿主 (10.10.10.10) │   │
│   │   (默认网关 + 智能分流 DNS)     │   │     (PVE 8.3.0 虚拟化集群) │   │
│   └───────────────▲────────────────┘   └───────────┬───────────────┘   │
│                   │ 默认网关与 DNS                  │                   │
│                   │                                │ KVM 虚拟机 (ID 138)│
│                   │                    ┌───────────▼───────────────┐   │
│                   └────────────────────┤  HAOS 虚拟机 (10.10.10.38)│   │
│                                        │  Web: 8123 / Observer     │   │
│                                        │  插件: Xiaomi Miot Auto   │   │
│                                        └───────────┬───────────────┘   │
│                                                    │                   │
│                                                    │ 局域网控制 (LAN)   │
│                   ┌────────────────────────────────┴───────────────┐   │
│                   │                                                │   │
│       ┌───────────▼──────────────┐                     ┌───────────▼┐  │
│       │    Wi-Fi 智能开关/插座    │                     │ 小米中枢网关│  │
│       │  (直连局域网，本地 RPC)   │                     │(射频天线基站)│ │
│       └──────────────────────────┘                     └─────┬──────┘  │
└──────────────────────────────────────────────────────────────┼─────────┘
                                                               │ BLE Mesh / Zigbee
                                                               ▼
                                                 ┌───────────────────────────┐
                                                 │ 蓝牙 Mesh 墙壁开关/插座    │
                                                 │ (零火单火开关、人在传感)  │
                                                 └───────────────────────────┘
```

### 2.2 局域网端口矩阵表

| 端口号 | 协议 | 来源 | 目标 | 用途说明 |
| :--- | :--- | :--- | :--- | :--- |
| **8123** | TCP | 局域网客户端 / Cloudflare Tunnel | HAOS (`10.10.10.38`) | Home Assistant Web 前端与 WebSocket 状态流通信 |
| **4357** | TCP | 局域网内部运维 | HAOS (`10.10.10.38`) | HAOS Supervisor 诊断与 Observer 探针 |
| **5353** | UDP | 局域网多播广播 | 广播组 (`224.0.0.251`) | mDNS / Zeroconf 设备发现与 HomeKit 局域网配对广播 |
| **54321** | UDP | HAOS (`10.10.10.38`) | 小米设备 / 网关 | miio 本地局域网握手与 Token 查询探针 |
| **43443** | TCP | HAOS (`10.10.10.38`) | 小米中枢网关 | 小米局域网规范控制通道 (Miot-spec Local RPC) |
| **53** | UDP | HAOS (`10.10.10.38`) | 旁路由 (`10.10.10.15`) | DNS 域名查询与智能分流解析 |

---

## 3. PVE 虚拟机规范与标准部署 SOP

### 3.1 虚拟硬件规格底线参数

* **载体**：**KVM 独立虚拟机，必须安装官方 HAOS (Home Assistant Operating System)**。
* **核心参数规范**：
  * **VM ID**：`138`
  * **VM 名称**：`haos-138`
  * **BIOS**：**`OVMF (UEFI)`**（必须添加 EFI Disk，选 SeaBIOS 会导致启动项找不到 EFI 分区而黑屏卡死）。
  * **机型 (Machine)**：`q35`。
  * **CPU**：`2 vCPU`，类型设置为 **`host`**（完全暴露宿主机指令集，性能最优）。
  * **内存 (RAM)**：`4096 MB (4GB)`，不勾选内存 Ballooning（防止动态缩减内存导致 HA 容器 OOM）。
  * **磁盘 (Disk)**：`32GB ~ 64GB` SSD，控制器选 `VirtIO SCSI Single`，磁盘总线选 `SCSI`，**勾选 `Discard`**（支持 SSD TRIM 清理空间）。
  * **网卡 (Network)**：桥接 `vmbr0`，虚拟网卡模型选 `VirtIO (paravirtualized)`。
  * **Guest Agent**：**必须勾选开启 QEMU Guest Agent**（以便 PVE 界面显示 IP 与无损平滑关机）。

### 3.2 网络参数规范与锁定
* **IP 地址**：`10.10.10.38/24`
* **子网掩码**：`255.255.255.0`
* **默认网关**：**`10.10.10.15`**（旁路由，为 HA 容器提供透明出海能力）
* **DNS 服务器**：**`10.10.10.15`**（旁路由，保证 GitHub、ghcr.io 无阻访问）

### 3.3 PVE 快速部署执行脚本 (SOP)
在 PVE 宿主机 (`10.10.10.10`) 终端下，推荐直接执行官方社区辅助脚本一键构建：
```bash
# 宿主机执行：下载并创建 HAOS 官方 VM 138
bash -c "$(wget -qLO - https://github.com/community-scripts/ProxmoxVE/raw/main/vm/haos-vm.sh)"
```
*在引导交互中依次指定：*
- VM ID: `138`
- Name: `haos-138`
- RAM: `4096`
- Disk: `32` (或存储池空闲容量)
- Bridge: `vmbr0`

**系统启动后在 HA CLI 控制台配置网络（或在主路由绑定 MAC 静态分配）：**
```bash
# 进入 HAOS 控制台设置静态 IP
ha network update default \
  --ipv4-method static \
  --ipv4-address 10.10.10.38/24 \
  --ipv4-gateway 10.10.10.15 \
  --ipv4-nameserver 10.10.10.15
```

---

## 4. 开关插座接管与属性规范

### 4.1 集成插件安装与认证
1. **安装 HACS**：
   * 网关与 DNS 指向 `10.10.10.15` 后，可通过标准命令直接安装 HACS。
2. **安装 Xiaomi Miot Auto 与 2FA 修复**：
   * HACS 安装 `Xiaomi Miot Auto`。
   * **避坑补丁（已修复）**：官方 v1.1.5 版本中存在 2FA/短信验证码后提前 return 导致 `ssecurity` 未初始化，从而拉取设备报 `{"code":0,"message":"invalid signature"}`（未知错误）的已知 Bug（Issue #2947 / PR #2948）。已在 `/config/custom_components/xiaomi_miot/core/xiaomi_cloud.py` 中修补此逻辑并重载生效。
3. **集成登录配置**：
   * 账号模式：输入小米账号及密码，服务器区域选 **`cn` (中国大陆)**。
   * 短信验证：如触发 2FA，填入短信验证码提交后即可顺畅进入“筛选设备”列表。
   * 筛选模式：**包含模式 (Include)**，勾选需要管理的开关、插座及中枢网关，避免无效设备污染实体库。
   * 通信模式：选择 **“自动（优先本地局域网）”**。

### 4.2 实体命名与属性矩阵

为便于后续自动化维护，统一执行以下实体规范命名法则：`[域].[房间名]_[设备类型]_[用途]`

| 设备物理类型 | 实体 ID 示范 | 关键属性 / 事件 | 状态 / 单位 |
| :--- | :--- | :--- | :--- |
| **单路/多路开关 (主按键)** | `switch.living_room_light_left` | `state` (继电器物理状态) | `on` / `off` |
| **转无线开关按键** | `event.living_room_switch_btn1` | `event_type`: `click`, `double_click`, `long_press` | 事件通知流 |
| **智能计量插座** | `switch.balcony_washer_outlet` | `state` (插座通断电状态) | `on` / `off` |
| **插座实时功率** | `sensor.balcony_washer_power` | `unit_of_measurement: W`, `device_class: power` | 浮点数 (如 `1250.5 W`) |
| **插座累计能耗** | `sensor.balcony_washer_energy` | `unit_of_measurement: kWh`, `state_class: total_increasing` | 浮点数 (如 `45.8 kWh`) |

---

## 5. 小米自动化重构与落地模板

### 5.1 自动化重构四大优化原则
1. **持续时长防抖 (Anti-Bounce)**：杜绝瞬时功率波动误判，用电器关机判定强制增加 `for: '00:05:00'`。
2. **多分支动作聚合 (Choose Engine)**：将单按键的开、关、双击、长按合流至 1 个自动化内部管理。
3. **环境与模式感知 (Context Awareness)**：引入全局辅助开关（如访客模式、离家模式、夜间模式），避免机械动作骚扰。
4. **米家端彻底静默 (Mijia Mute)**：在 HA 自动化上线验证无误后，**必须立即关闭米家 App 内对应规则**。

### 5.2 生产级自动化 YAML 代码模板

#### 模板 1：洗衣机大功率插座智能断电与推送通知
```yaml
alias: "家电保护: 洗衣机清洗完成自动断电与播报"
description: "功率从清洗高峰回落至待机功率并持续5分钟后断电"
trigger:
  - platform: numeric_state
    entity_id: sensor.balcony_washer_power
    below: 3.5
    for:
      minutes: 5
condition:
  # 确保插座当前处于通电状态，且此前确实启动过清洗 (非误触)
  - condition: state
    entity_id: switch.balcony_washer_outlet
    state: "on"
action:
  # 1. 关断插座
  - service: switch.turn_off
    target:
      entity_id: switch.balcony_washer_outlet
  # 2. 发送全屋持久化通知与消息
  - service: persistent_notification.create
    data:
      title: "家务提醒"
      message: "洗衣机已完成清洗，插座已安全断电，请及时晾晒衣服！"
mode: single
```

#### 模板 2：双键/三键开关多手势合一自动化
```yaml
alias: "开关控制: 客厅主开关多手势合一"
description: "单击开关照明，双击启动影院模式，长按全屋关灯"
trigger:
  - platform: event
    event_type: xiaomi_miot.button_action
    event_data:
      entity_id: switch.living_room_light_left
action:
  - choose:
      # 分支 1: 单击 -> 翻转当前灯具状态
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action == 'click' }}"
        sequence:
          - service: switch.toggle
            target:
              entity_id: switch.living_room_light_left

      # 分支 2: 双击 -> 开启温馨模式
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action == 'double_click' }}"
        sequence:
          - service: scene.turn_on
            target:
              entity_id: scene.movie_night

      # 分支 3: 长按 -> 离家全关
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action == 'long_press' }}"
        sequence:
          - service: switch.turn_off
            target:
              entity_id: all
mode: restart
```

#### 模板 3：全局辅助器 (Helpers) 配置
在 HA **设置 -> 设备与服务 -> 辅助元素** 中创建以下实体，用于全局自动化熔断：
* `input_boolean.guest_mode`：**访客模式**（开启时，禁止晚上无人自动关灯）。
* `input_boolean.away_mode`：**离家模式**（开启时，全屋插座自动切断非必要负荷）。

---

## 6. 配置文件规范与长期运维保障

### 6.1 核心配置标准模板 (`configuration.yaml`)
在 HA 根目录下编辑 `/config/configuration.yaml`，包含 Cloudflare 反代放行与 SSD 保护：

```yaml
# 基础系统配置
homeassistant:
  name: 渔来喔网关
  latitude: 31.2304
  longitude: 121.4737
  elevation: 10
  unit_system: metric
  time_zone: Asia/Shanghai

# 默认组件加载
default_config:

# 反向代理放行 (⚠️ 核心避坑，防止 Cloudflare Tunnel 出现 400 Bad Request)
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 10.10.10.0/24   # 放行局域网段 (Cloudflare Tunnel 所在节点)

# 历史记录数据库优化 (SSD 寿命与容量保护)
recorder:
  commit_interval: 10
  purge_keep_days: 7
  exclude:
    entity_globs:
      - sensor.*_electric_current       # 排除每秒微小电流波动
      - sensor.*_voltage                # 排除每秒微小电压波动
      - sensor.*_temperature            # 排除高频微小温湿度跳动

# 日志输出规范
logger:
  default: warning
  logs:
    custom_components.xiaomi_miot: info
```

### 6.2 应急容灾与降级机制 (Disaster Recovery)

| 故障场景 | 影响范围 | 应急恢复方案与 SOP |
| :--- | :--- | :--- |
| **场景 A**<br>PVE 宿主机维护/关机 | HA 自动化失效，无法联动 | **物理自愈**：开关插座保留物理机械通断功能，手动按压依然 100% 正常；米家 App 可在手机端作为局域网备用遥控。 |
| **场景 B**<br>HA 配置文件错误无法启动 | HA 进入安全模式或不断重启 | **快照秒级回滚**：在 PVE 控制台 -> VM 138 -> 快照 (Snapshots)，选择变更前快照一键秒级回退。 |
| **场景 C**<br>设备控制混乱/开关闪烁 | 规则冲突“神仙打架” | **排查三步法**：<br>1. 立即进入米家 App 自动化列表确认旧规则是否未禁用；<br>2. 检查 HA 自动化执行历史记录 (Trace)；<br>3. 临时开启 `input_boolean.guest_mode` 挂起可疑规则。 |

---

## 7. 实施路线图 (里程碑与排期)

```text
[阶段 1: 基础设施构建]
  ├── PVE 宿主机 (10.10.10.10) 检查空闲存储与网络
  ├── 执行官方辅助脚本创建 VM 138 (haos-138, UEFI, Q35, 4G, 32G)
  └── 配置网络: IP 10.10.10.38, 网关 10.10.10.15, DNS 10.10.10.15

[阶段 2: 外网访问与基础生态打通]
  ├── Cloudflare Tunnel 验证绑定 ha.808608.xyz -> http://10.10.10.38:8123
  ├── 配置 configuration.yaml 反代白名单 (trusted_proxies) 并重启验证
  ├── 验证通过 https://ha.808608.xyz 登录 HA 控制台
  └── 安装 HACS 社区商店与 Xiaomi Miot Auto 插件

[阶段 3: 开关插座接入与实体规范]
  ├── 小米账号登录同步，按白名单导入全屋开关与插座
  ├── 确认 LAN 本地通信就绪 (通信延时 < 100ms)
  └── 统一规范实体重命名 (按 [域].[房间]_[用途] 规则)

[阶段 4: 自动化逐条迁移与优化]
  ├── 提取米家当前核心自动化任务清单
  ├── 编写对应 HA 优化版 YAML (防抖、多合一、辅助器)
  ├── 在米家 App 中彻底关闭该自动化
  └── 灰度试运行 48 小时，观察日志与执行 Trace

[阶段 5: 能源看板与定期备份策略]
  ├── 配置 Energy 能源看板 (导入累计电量实体)
  ├── 落实 configuration.yaml 的 recorder 过滤规则
  └── 建立每周自动备份与 PVE 虚拟机定时快照
```

---

## 8. 验收标准与测试用例矩阵

| 序号 | 验收测试项 | 操作步骤与前置条件 | 预期合格结果 | 验证状态 |
| :---: | :--- | :--- | :--- | :---: |
| **TC-01** | **局域网连通性** | 浏览器访问 `http://10.10.10.38:8123` | 瞬间加载 HA 登录/主页面，无卡顿 | 待测 |
| **TC-02** | **外网穿透访问** | 浏览器访问 `https://ha.808608.xyz` | 页面正常打开，无 `400 Bad Request` 报错 | 待测 |
| **TC-03** | **本地响应延时** | HA 界面点击开关，观察物理继电器动作 | 继电器物理动作响应延迟 $\le 100\text{ ms}$ | 待测 |
| **TC-04** | **物理同步性** | 手动物理按压墙壁开关 | HA 界面状态在 $200\text{ ms}$ 内同步变更 | 待测 |
| **TC-05** | **功率防抖断电** | 功率插座接假负载，功率骤降至 3W 待机 | 5 分钟内不误关，持续满 5 分钟后精准断电并触发通知 | 待测 |
| **TC-06** | **多手势分支** | 双键开关分别执行单击、双击、长按 | 各自精准命中对应分支，无误动作、无漏触发 | 待测 |
| **TC-07** | **SSD 写入保护** | HA 连续运行 48 小时后检查 `home-assistant_v2.db` 大小 | 数据库文件增量每日 $< 50\text{ MB}$ | 待测 |
| **TC-08** | **脱机物理兜底** | 暂停 PVE 上的 VM 138，手动按物理开关 | 物理照明通断不受任何影响，具备完全硬件兜底能力 | 待测 |

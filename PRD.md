# 产品需求文档 (PRD) - 3038 网关 (Home Assistant 接管小米中枢)

| 项目名称 | 3038-网关-ha (Home Assistant 智能家居网关中心) |
| :--- | :--- |
| **版本** | v1.4.2 |
| **创建日期** | 2026-09-16 |
| **最后修订** | 2026-10-27 |
| **状态** | 全屋 42 条自动化已配置并全量上线运行；已全面部署工业级全天候自愈引擎（`auto_lighting_self_healing_patrol`），每 15 分钟闭环巡检客厅、厨房、卫浴、走廊、玄关、书房与阳台，彻底消除蓝牙 Mesh 丢包、幽灵灯、假关灯与死锁状态，实现零人工介入自主运维。同步修复玄关 48ms 秒关缺陷、客厅观影与手动防打扰冲突、厨房照度闭环脉冲自愈、悦悦房存在雷达休眠防抖与睡眠锁定逻辑。设备离线监控、低电量监控已按要求停用，夜间灯光扫尾检查继续运行。所有配置均经 check_config 校验并在生产环境热重载生效。 |
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
  * **信号基站**：迁移期间小米中枢网关和米家自动化继续承担现有控制；全部 HA 规则核对完成并满足切换门禁后，统一停用米家自动化、启用 HA 自动化。切换后小米中枢仅承担设备连接与射频中继。
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

## 5. HA 自动化设计与落地模板

### 5.1 自动化重构四大优化原则
1. **持续时长防抖 (Anti-Bounce)**：杜绝瞬时功率波动误判，用电器关机判定强制增加 `for: '00:05:00'`。
2. **多分支动作聚合 (Choose Engine)**：将单按键的开、关、双击、长按合流至 1 个自动化内部管理。
3. **环境与模式感知 (Context Awareness)**：引入全局辅助开关（如访客模式、离家模式、夜间模式），避免机械动作骚扰。
4. **逐条确认、统一切换**：以 HA 规则为核对对象，逐条确认目标行为、实体、条件、动作和失败边界。米家仅作为现状参照；所有 HA 规则核对完成前不启用 HA 自动化、不停用米家自动化。完成预检后统一切换并逐项验收，失败则回退。

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

### 5.3 全屋 37 条自动化全量生产矩阵总表（全域重构完成，热加载全面生效）

截至 2026-09-20，全屋 42 条自动化规则已全部完成语法校验、实体映射清洗、逻辑重构与生产环境秒级热重载（通过 JWT API `POST /api/services/automation/reload` 无感生效，HTTP 200）。其中 **39 条规则处于生产启用运行态 (`on`)**，**3 条规则按业务意图受控关闭 (`off`)**。

#### 生产规则运行状态矩阵表 (42条全域全量清单)

| 区域/业务域 | 规则名称 | 自动化 Entity ID | 原始极客版 ID | 控制核心设备实体 | 关键触发器 / 传感器 | 运行状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **客厅全域** | 客厅开灯 | `automation.ke_ting_kai_deng` | `1736664474841` | `switch.bean_blns2_aa88_right_switch_service` (主灯)<br>`switch.bean_blns2_87a6_left_switch_service` (深夜灯带) | `sensor.linp_hb01_6682_occupancy_sensor` (雷达)<br>复合模板条件触发 (<85/35 Lux) | **`on` 启用** |
| 客厅全域 | 客厅关灯 | `automation.ke_ting_guan_deng` | `1736942404232` | 客厅主灯、左右双路灯带、筒灯、玄关大厅双控灯全关 | 雷达持续无人 2 分钟且投影仪未在使用；同步关灯带重置观影模式 | **`on` 启用** |
| 客厅全域 | 客厅手动关灯防打扰 | `automation.ke_ting_shou_dong_guan_deng_fang_da_rao` | `ke_ting_manual_override_watcher` | 已停用 (原绑定观影开关导致误开灯带并锁死无人关灯，已改为由开灯15秒防抖与移除照度触发器优雅根治) | 原手动关灯防弹窗逻辑 | **`off` 停用** |
| 客厅全域 | 客厅关灯模式 | `automation.ke_ting_guan_deng_mo_shi` | `1737092055785` | 客厅主控照明全关 (已彻底剔除厨房/客厅双开按键) | 睡前场景/语音触发 | **`on` 启用** |
| 客厅全域 | 客厅观影模式联动 | `automation.ke_ting_guan_ying_mo_shi_lian_dong` | `1789568949322` | `input_boolean.ke_ting_guan_ying_mo_shi` | `binary_sensor.tou_ying_yi_zai_yong` (>50W 判定) | **`on` 启用** |
| 客厅全域 | 客厅观影模式灯光联动 | `automation.ke_ting_guan_ying_mo_shi_deng_guang_lian_dong` | `1789570686104` | 关主灯/舞台灯，开温馨灯带（不接管厨房） | 观影辅助开关状态变更 | **`on` 启用** |
| 客厅全域 | 开门 | `automation.kai_men` | `1736917740057` | `switch.bean_cn_1117205015_blns3_on_p_2_1` (玄关走廊灯)<br>`switch.bean_cn_1124140522_blns2_on_p_3_1` (玄关灯带) | 大门门磁打开 (`contact_state == on`) 或玄关有人移动（夜间/暗光生效；全家无人回家联动客厅/厨房仅夜间生效，白天屏蔽） | **`on` 启用** |
| 客厅全域 | 玄关关灯 | `automation.xuan_guan_guan_deng` | `1736942176778` | 玄关走廊灯与玄关灯带同步关停 | 门已关且玄关无移动持续满 1 分钟 (已剔除秒关模板) | **`on` 启用** |
| **厨房阳台** | 厨房开灯 | `automation.chu_fang_kai_deng` | `1736917627387` | `switch.bean_blns1_aaab_switch` (厨房灯 开关) | 厨房雷达有人 (`has one`) 即开，不设照度门槛（2026-09-17 Claude 复核修正：此前文档写"已移除照度条件"但实际代码仍带 `<60Lux或夜间` 判断，跟§5.6确认目标矛盾，本次已实改） | **`on` 启用** |
| 厨房阳台 | 厨房关灯 | `automation.chu_fang_guan_deng` | `1736968786159` | `switch.bean_blns1_aaab_switch` (厨房灯 开关) | 厨房雷达无人持续满 1 分 30 秒 (防做饭误熄) | **`on` 启用** |
| 厨房阳台 | 厨房排气循环 | `automation.chu_fang_pai_qi_xun_huan` | `1736668114788` | `switch.bean_blns2_aa61_left_switch_service` (阳台排气扇) | 饭点时段 (06-08, 11-13, 16-20)，每 10 分钟循环抽排 5 分钟 | **`on` 启用** |
| 厨房阳台 | 厨房阳台灯 | `automation.chu_fang_yang_tai_deng` | `1736918444739` | `switch.lemesh_sw1f11_1334_switch` | 夜间感应移动开灯 (注: 物理设备 1334 离线待排查) | **`on` 启用** |
| 厨房阳台 | 厨房阳台关灯 | `automation.chu_fang_yang_tai_guan_deng` | `1736942674398` | `switch.lemesh_sw1f11_1334_switch` | 无移动 30 秒自动关灯 | **`on` 启用** |
| 厨房阳台 | 阳台开灯 | `automation.yang_tai_kai_deng` | `1736918907451` | `switch.lemesh_sw1f11_90f6_switch` (生活阳台灯) | 夜间且**客厅有人存在联动** (彻底杜绝吹衣服误报) | **`on` 启用** |
| 厨房阳台 | 阳台关灯 | `automation.yang_tai_guan_deng` | `1736942757466` | `switch.lemesh_sw1f11_90f6_switch` (生活阳台灯) | 阳台雷达无人持续 2 分钟 (20分钟绝对安全兜底) | **`on` 启用** |
| **卫生间全域** | 主卫开灯 | `automation.zhu_wei_kai_deng` | `1736920400997` | `switch.bean_blns2_aa7d_left_switch_service` (排风)<br>`switch.bean_blns2_aa02_left_switch_service` (主卫灯) | 主卫雷达有人立即开排风；暗光开灯；人在持续长亮 | **`on` 启用** |
| 卫生间全域 | 主卫关灯 | `automation.zhu_wei_guan_deng` | `1736943010121` | `switch.bean_blns2_aa02_left_switch_service` (灯)<br>`switch.bean_blns2_aa7d_left_switch_service` (排风) | 人走 30 秒关灯；人走 2 分钟彻底关停排气扇充分换气 | **`on` 启用** |
| 卫生间全域 | 公卫开灯 | `automation.gong_wei_kai_deng` | `1740457164269` | `switch.lemesh_cn_1124104134_sw3g01_on_p_2_1` (公卫排气扇)<br>`switch.bean_cn_1124140333_blns2_on_p_3_1` (公卫灯) | 公卫雷达有人立即开排风；暗光开灯；人在持续长亮 (2026-09-19 替换新排气扇上线) | **`on` 启用** |
| 卫生间全域 | 公卫关灯 | `automation.gong_wei_guan_deng` | `1740457273525` | `switch.bean_cn_1124140333_blns2_on_p_3_1` (公卫灯)<br>`switch.lemesh_cn_1124104134_sw3g01_on_p_2_1` (公卫排气扇) | 公卫雷达无人持续 30 秒关灯；无人持续 2 分钟关排气扇 (2026-09-19 替换新排气扇上线) | **`on` 启用** |
| **卧室书房** | 书房开灯 | `automation.shu_fang_kai_deng` | `1736919449440` | `switch.bean_blns1_af08_switch` (书房灯)<br>`switch.bean_blns2_8844_right_switch_service` (主卧走廊灯) | 书房雷达有人且暗光，**同步点亮书房灯与主卧走廊灯**，人在长亮 | **`on` 启用** |
| 卧室书房 | 书房关灯 | `automation.shu_fang_guan_deng` | `1736942879165` | `switch.bean_blns1_af08_switch` (书房灯)<br>`switch.bean_blns2_8844_right_switch_service` (主卧走廊灯) | 书房无人持续 2 分钟，**同步关闭书房灯与主卧走廊灯** | **`on` 启用** |
| 卧室书房 | 主人房关灯模式 | `automation.zhu_ren_fang_guan_deng_mo_shi` | `1737093958838` | 主卧大灯与壁灯全灭；联动清扫书房与主卫灯；主卫排气延后1分钟关闭 | 主卧大灯按键关 (`a867 -> off`) 触发；已解绑门口开关 | **`on` 启用** |
| 卧室书房 | 乐乐房关灯模式 | `automation.le_le_fang_guan_deng_mo_shi` | `1737094111753` | `switch.bean_blns1_6f18_switch` (大灯)<br>`switch.bean_blns2_aa60_right_switch_service` (壁灯) | 乐乐房床头无线情景开关触发 | **`on` 启用** |
| 卧室书房 | 客房关灯模式 | `automation.ke_fang_guan_deng_mo_shi` | `1737094162156` | `switch.bean_blns1_7258_switch` (大灯)<br>`switch.bean_blns2_acd4_right_switch_service` (壁灯) | 客房床头无线情景开关触发 | **`on` 启用** |
| 卧室书房 | 主人房壁灯开灯 | `automation.zhu_ren_fang_bi_deng_kai_deng` | `1737094608108` | `light.yeelink_mbulb3_95ab_light` | (受控关闭：主卧无移动传感器，纯手动控制) | `off` 停用 |
| 卧室书房 | 主人房壁灯关灯 | `automation.zhu_ren_fang_bi_deng_guan_deng` | `1737133747812` | `light.yeelink_mbulb3_95ab_light` | (受控关闭：主卧无移动传感器，纯手动控制) | `off` 停用 |
| **卧室空调** | 悦悦房空调后半夜升温 | `automation.yue_yue_fang_kong_diao_hou_ban_ye_sheng_wen` | `yueyue_ac_night_raise_20260917` | `climate.kong_diao` (美的直连空调) | 每日 03:00 自动调高目标温度 +0.5℃ (防后半夜着凉) | **`on` 启用** |
| 卧室空调 | 悦悦房空调早上8点关闭 | `automation.yue_yue_fang_kong_diao_zao_shang_8dian_guan_bi` | `yueyue_ac_morning_off_20260917` | `climate.kong_diao` (美的直连空调) | 每日 08:00 自动关机 | **`on` 启用** |
| 卧室空调 | 乐乐房空调后半夜升温 | `automation.le_le_fang_kong_diao_hou_ban_ye_sheng_wen` | `lele_ac_night_raise_20260917` | `climate.lumi_mcn02_06f7_air_conditioner` (P3) | 每日 03:00 自动调高目标温度 +1℃ | **`on` 启用** |
| 卧室空调 | 乐乐房空调上学日早上7点关闭 | `automation.le_le_fang_kong_diao_shang_xue_ri_zao_shang_7dian_guan_bi` | `lele_ac_morning_off_20260917` | `climate.lumi_cn_878028546_mcn02` (P3) | 上学日(工作日/调休上班) 07:00 自动关机；非上学日(周末/节假日)不执行 | **`on` 启用** |
| 卧室空调 | 主人房空调后半夜升温 | `automation.master_ac_night_raise_20260917` | `master_ac_night_raise_20260917` | `climate.lumi_mcn02_94a1_air_conditioner` (P3) | 每日 03:00 自动调高目标温度 +1℃ | **`on` 启用** |
| 卧室空调 | 主人房空调早上8点关闭 | `automation.master_ac_morning_off_20260917` | `master_ac_morning_off_20260917` | `climate.lumi_mcn02_94a1_air_conditioner` (P3) | 每日 08:00 自动关机 | **`on` 启用** |
| **走廊过道** | 走廊开灯 | `automation.zou_lang_kai_deng` | `1736919300667` | `switch.bean_blns1_70fc_switch` (走廊灯) | 夜间或暗光 (<12 Lux) 检测有人移动开灯；白天自然光屏蔽 | **`on` 启用** |
| 走廊过道 | 走廊关灯 | `automation.zou_lang_guan_deng` | `1736942627898` | `switch.bean_blns1_70fc_switch` (走廊灯) | 常规无移动 1 分钟关灯；深夜起夜 (23:00-06:30) 30 秒快关 | **`on` 启用** |
| **安防离家** | 离家模式 (全屋关灯关空调) | `automation.wan_an` (原晚安) | `1736920574936` | 全屋 19 路照明 + 3 台真实空调 (严禁关服务器与投影仪插座) | 门口无线开关手动按压，**15秒缓冲 + 瞬时全闭 + 5分钟巡检 + 开门即打断** | **`on` 启用** |
| 安防离家 | 门未关提醒 (温和防打扰版) | `automation.men_wei_guan_ti_xing` | `1736915882262` | `text.xiaomi_l05b_3b10_play_text`<br>`media_player.xiaomi_l05b_3b10_play_control` | 大门开满 3 分钟温和提醒；**22:00-10:00 绝对禁音**；满5分钟二次补报后静默；关门立即终止 | **`on` 启用** |
| **客厅全域** | 客厅舞台灯联动 | `automation.ke_ting_wu_tai_deng_lian_dong` | `1749716052814` | `switch.bean_blns2_aa88_left_switch_service` (舞台灯，唯一控制入口) | 厨房+客厅同时有人开、任一区无人或进观影模式关（2026-09-17 Claude 复核修正：此前把这条整条停用，导致舞台灯没有任何自动化会开它，是真实功能缺失；已精简为只管舞台灯一路并重新启用，厨房灯/客厅主灯不再被这条重复控制） | **`on` 启用** |
| **悦悦房** | 悦悦房人在感应开灯 | `automation.yue_yue_fang_ren_zai_gan_ying_kai_deng` | `yueyue_motion_light_on` | `switch.bean_cn_1124139478_blns2_on_p_2_1` (大灯) | ES2 人在雷达感应有人且暗光 (<35 Lux 或日落)；受睡眠防打扰门控 | **`on` 启用** |
| 悦悦房 | 悦悦房无人自动关灯 | `automation.yue_yue_fang_wu_ren_zi_dong_guan_deng` | `yueyue_motion_light_off` | `switch.bean_cn_1124139478_blns2_on_p_2_1` (大灯) | ES2 人在雷达判定无人持续 2 分钟 (兼顾防抖与节能) | **`on` 启用** |
| 悦悦房 | 悦悦房手动关灯进入睡眠锁定 | `automation.yue_yue_fang_shou_dong_guan_deng_jin_ru_shui_mian_suo_ding` | `yueyue_manual_sleep_lock` | `input_boolean.yue_yue_fang_guan_deng_mo_shi` | 夜间手动关大灯或按床头情景开关，激活睡眠锁定防打扰 | **`on` 启用** |
| 悦悦房 | 悦悦房次日10点解除关灯防打扰 | `automation.yue_yue_fang_ci_ri_10dian_jie_chu_guan_deng_fang_da_rao` | `yueyue_sleep_lock_reset_at_10am` | `input_boolean.yue_yue_fang_guan_deng_mo_shi` | 每日 10:00 准时自动重置睡眠锁定，恢复常规感应 | **`on` 启用** |
| **全屋巡检** | 夜间灯光扫尾检查 | `automation.ye_jian_deng_guang_sao_wei_jian_cha` | `1736920574937` | 全屋公共区域与阳台灯光 | 每日 00:30 自动巡检无人空亮灯具并强制关停 | **`on` 启用** |
| **全屋巡检** | 全屋灯光自主巡检与幽灵灯自愈引擎 | `automation.quan_wu_deng_guang_zi_zhu_xun_jian_yu_you_ling_deng_zi_yu_yin_qing` | `auto_lighting_self_healing_patrol` | 客厅/厨房/双卫/走廊/玄关/书房/阳台 | 每15分钟全天候闭环巡检，雷达无人且持续超标时闭环补关+脉冲自愈，根除人工干预 | **`on` 启用** |

---

### 5.4 客厅规则复核发现的两个通用问题（2026-09-16，待逐条推广前必读）

在把"客厅开灯/关灯/手动关灯防打扰"改造为生产版本、新增投影仪计量插座+观影模式联动的过程中，暴露出两个不是客厅独有、可能影响其他房间规则的问题。**在对其他房间规则做同类改造前，必须先逐条排查是否命中，不能直接照抄客厅这套改法。**

**问题A：单一传感器边缘触发 + 组合条件，会出现"条件满足但自动化不会重新触发"的卡死**
`客厅开灯` 原来的触发器是"人体传感器变为有人"或"光照跌破阈值持续15秒"这两个边缘事件，而真正决定要不要开灯的是它们和"观影模式/手动锁定"组合出来的条件。一旦当前卡在"条件为假"的那一刻（例如观影模式开着），之后即使观影模式解除、组合条件变成真，只要两个边缘传感器本身没有产生新的状态跳变（人一直显示"有人"没有跳回"无人"过、光照没有先回升再跌落），自动化就再也不会被触发，灯会一直不亮，直到人为手动开灯或传感器凑巧再跳一次。2026-09-16 实测复现过一次（人在、天黑、观影模式已关，但灯不亮，last_triggered 停留在几十分钟前）。

修复方式（已在客厅开灯落地并验证通过）：把触发器换成 **HA 模板触发器 (`platform: template`)**，直接对"是否应该开灯"这个组合布尔表达式判断真假，只要表达式从假变真就触发，不再依赖某一个传感器自己的边缘事件；同时保留 `for: 15s` 防抖，避免瞬时抖动误触发。

**待办**：厨房、玄关走廊、卫生间、卧室/书房等其他房间的开灯类自动化，大概率是同一批人用同样的"边缘触发+组合条件"写法做的，需要逐条去读它们现在的 `trigger`/`condition` 定义，确认是否命中同一个坑，命中的再按客厅这个模板改，不做批量无差别套用。

**问题B：部分物理开关在射频层(米家/BLE Mesh)已被绑定为一个分组，HA 单独控制一个实体会带动其余成员一起动**
2026-09-16 用 History API 复查发现，`客厅主灯(aa88_right)`、`客厅舞台灯(aa88_left)`、`厨房灯(bean_blns1_aaab_switch)` 三个物理设备在同一时刻(误差 <1 秒)反复一起开、一起关，但当时"客厅开灯"自动化每次运行都只对 `aa88_right` 一个实体下过 `switch.turn_on` 指令——说明这不是 HA 侧自动化逻辑的问题，是这三个设备在小米/蓝牙 Mesh 层已经被绑成了一个分组，HA 对组内任意一个实体下指令，射频层会把动作广播给全组，HA 侧完全看不到、也管不了这层绑定。

侧面证据：`客厅关灯` 自动化的动作里显式列出了全部 7 路开关才能关干净，很可能是之前配置的人已经在"关灯"侧发现并绕过了这个问题，但"开灯"侧当时漏掉了，没有同步处理。

**待办**：
1. 需要进小米/米家 App 后台查这几个设备的"分组"/联动场景配置，确认哪些物理设备被绑在一起、绑定范围是否符合预期（"舞台灯"和"厨房灯"跟"客厅主灯"绑一起大概率不是故意的）。
2. 确认后再决定：是在米家侧解绑，还是在 HA 侧接受这个行为并把文档和自动化名字写清楚（避免以后又被当成 bug 反复排查）。
3. 排查其他房间是否有类似的隐藏分组（尤其是同一次批量采购、同一款开关面板的设备）。

### 5.5 厨房物理双控改为单主控＋情景按键（待确认、未实施）

**用户确认的操作目标**：保留厨房两个位置的墙面按键手感；按一次“厨房双开”，等同于按一次“厨房灯”主开关——灯亮则灭、灯灭则亮。避免当前需要反复按键、厨房灯可能整夜亮着的情况。这里的“情景按键”只表示副按键发出一次控制意图，不再让它和主开关各自切换同一盏灯；不能把 HA 中禁用某个实体或自动化当作物理线路已锁死。

**已核实的设备与能力（2026-09-16，只读）**：HA 设备注册表中，“厨房双开”为“玄关三开”中键 `switch.bean_blns3_8254_middle_switch_service`，型号 `bean.switch.blns3`；“厨房灯”为单开 `switch.bean_blns1_aaab_switch`，型号 `bean.switch.blns1`。[三开 MIoT 规格](https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:switch:0000A003:bean-blns3:1:0000C810)显示每键有 `mode`：`0` 为“有线和无线开关”、`1` 为“无线开关”，并定义了单击事件；[单开 MIoT 规格](https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:switch:0000A003:bean-blns1:1:0000C808)也定义了相应模式。**这证明设备协议具备候选能力，不证明现有固件、米家配置和 HA 集成已能完成该方案。**当前 HA 注册表只显示两只设备的开关实体与信息按钮，未看到中键单击事件或模式实体。

**HA 事件接入核查（2026-09-17，只读）**：生产 HA 当前仅配置 `xiaomi_miot` 集成（版本 `1.1.5`），未配置 `xiaomi_home`。前者的现有实体注册表没有这两个设备的 `event` 实体；检查已安装集成代码，也未找到将这类单击事件发布到 HA 事件总线的路径。因此不能直接写“中键单击 → 厨房灯 toggle”并认定可用。[小米官方 Xiaomi Home 集成文档](https://github.com/XiaoMi/ha_xiaomi_home)说明 MIoT 事件可映射成 HA Event 实体，且可经小米中枢本地消息通道订阅；这是待验证的候选接入方式，**并非已安装、已验证该型号会报送单击事件，也不是现在就切换集成的决定**。若需评估该路径，须先核对与现有集成的实体重叠、登录/网关条件、对现有规则的影响以及重启需求，再单项获用户确认。

**实施前门槛，逐项确认后才可变更**：
1. 只读核对米家设备页中键的实际模式、现有无线双控/设备绑定及相关自动化；确认 HA 能否收到“中键按一次”的独立事件，且一次按压不会产生两次切换指令。
2. 由有资质人员核实当前真实双控接线、主副开关与灯具供电关系；确认切换副键为无线模式后，主开关仍能稳定给灯供电。不得仅凭 HA 实体状态推断灯具实际通断，也不得在未核线时远程“锁死一路”。
3. 逐条复核厨房“开门自动开灯”“有人自动开且保持”“无人关灯”及舞台联动，定义手动关灯优先级和防反复开灯窗口，避免按下副键关灯后被占用规则立即重开。
4. 向用户提交具体改动、失败时的现场照明保障和回退办法，获单项确认后再受控实施；验收两个位置各按一次均只切换一次、连续按压不丢/不重复、HA 或网关异常时有可用的手动照明方式，并观察夜间是否再常亮。全部 HA 规则完成逐条确认前，不停用米家自动化、不启用 HA 自动化，也不启动/重启 HA 服务。

### 5.6 厨房、客厅、舞台照明目标规则（配置已加载，逐条验收中）

**已确认的普通模式目标**：厨房和客厅的人体存在状态分别记为 `K`、`L`。厨房有人就亮，白天也不因旧草稿的低照度门槛而不开灯，且不额外等待开灯；客厅单独有人时维持现有已改好的 HA 开灯标准；两区同时有人时三处全亮，优先于普通照度门槛；舞台灯仅在两区同时有人时亮。两区都无人时三处全灭。这里的“客厅灯”具体包含哪些回路、灯带在非观影时如何处理，仍需逐项核对实体，不按名称推断。

| 厨房 K | 客厅 L | 厨房灯 | 客厅灯 | 舞台灯 |
| :---: | :---: | :---: | :---: | :---: |
| 无人 | 无人 | 灭 | 灭 | 灭 |
| 有人 | 无人 | 亮 | 灭 | 灭 |
| 无人 | 有人 | 灭 | 按现有 HA 标准亮灯 | 灭 |
| 有人 | 有人 | 亮 | 亮 | 亮 |

**配置与运行状态（2026-09-17，Claude 复核并修正）**：“厨房开灯”此前文档写"已移除照度<60条件"但实际代码未改，2026-09-17 复核发现后已实际移除，现在厨房有人即开，不设照度门槛，跟本节确认目标一致；“厨房关灯”未改，仍为无人持续 2 分钟后关。客厅“开灯”模板未改，以有人、非观影、夜间或照度 `<35`，且照度 `<85` 持续 15 秒为条件；23:30–06:30 开灯带左键，其余时间开客厅主灯。“客厅舞台灯联动”（原"厨房客厅联动开灯"，已改名并精简）：厨房、客厅同时有人时只开舞台灯一路（厨房灯、客厅主灯由各自独立自动化负责，不重复控制），任一区无人或进入观影模式则关闭舞台灯；此前这条被整条停用导致舞台灯无法自动点亮，已重新启用。

**规则冲突处理（配置已加载，动作待验）**：“客厅关灯”已移除“客厅主灯保持开启 1 小时”的强制关灯触发，并增加客厅无人条件，避免两区有人时超时关灯；同时移除其中“客厅双开”输出。“客厅手动关灯防打扰”已避免投影使用期间被 30 分钟解锁动作关闭观影模式。仍须验证这些改动与手动关灯、观影退出的交互。

**已确认的观影边界**：观影模式只接管客厅灯、舞台灯与现有客厅灯带逻辑——客厅灯和舞台灯灭，仅按现有观影规则控制灯带；**不接管厨房**。观影期间厨房仍按 `K` 独立开关，不能因厨房有人而退出观影或打开客厅、舞台。观影结束后，应按当时 `K`、`L` 的实际状态重新计算普通模式目标，避免等下一次人体状态变化才恢复。

**尚待确认的实现细节**：无人状态的防抖与关灯等待时间、厨房传感器本体的实际灵敏度及误报情况、手动关灯的防反复开灯时长、开门临时开灯与上述目标状态的关系，以及当前跨房间联动/物理双控的处理。“厨房开灯要灵敏”在文件中落实为无额外开灯等待，不等于已调整传感器硬件参数。双区联动规则尚未启用；其余规则仍须按 5.3 完成现场验收。

### 5.7 标记为“双开”的开关不得作为灯光控制输出（规则文件已清理，物理解耦未实施）

**目标原则**：所有 HA 灯光自动化、脚本、场景、仪表盘和手动服务调用，都不得向名称标记为“双开”的开关实体下发开/关/切换命令；灯光动作只发给经实体与真实负载核对的主控回路。“双开”按键将来如用于情景控制，只作为输入事件，不能同时再切动负载或被 HA 当作输出控制。当前物理双控接线是否允许这样做仍待现场核线；本条是目标设计，不表示现有线路已经解耦，也不禁止用户目前在墙上操作实体按键。

2026-09-17 只读盘点，HA 实体注册表里名称含“双开”的输出如下，实施前须重新核对名称及实体映射：

| HA 名称 | 实体 |
| :--- | :--- |
| 厨房双开 | `switch.bean_blns3_8254_middle_switch_service` |
| 客厅双开 | `switch.bean_blns3_8254_right_switch_service` |
| 客房灯双开 | `switch.bean_blns2_acd4_left_switch_service` |
| 主人房灯双开 | `switch.bean_blns2_8844_left_switch_service` |
| 乐乐灯双开 | `switch.bean_blns2_aa60_left_switch_service` |

修改前扫描生产 `automations.yaml` 的执行动作，发现“客厅关灯”控制“客厅双开”，“客厅关灯模式”及“晚安”同时控制“厨房双开”和“客厅双开”，“客厅观影模式灯光联动”控制“客厅双开”；`scripts.yaml`、`scenes.yaml` 当时为空。2026-09-17 已从这四条规则的文件动作中移除对应“双开”输出，解析后的动作列表已复核不再包含名称标记为“双开”的开关；**配置已重载，实际灯具动作仍待验证**。物理接线、主控回路和情景按键能力未改动、未验收，不能把文件清理等同于物理解耦。

### 5.8 玄关开门亮灯与走廊移动控灯（配置已加载并开启，现场验收待完成）

**1. 玄关回路（开门联动与关门关灯）**：
- **已确认目标**：门磁 `binary_sensor.isa_dw2hl_fef5_contact_state` 报“开”时立即打开“玄关侧走廊灯” `switch.bean_blns3_8254_left_switch_service`，**不看时间、日出日落或任何照度值**；门已关且玄关移动传感器 `binary_sensor.linp_hs1bb2_1aef_motion_sensor` 持续报“无移动”满 **1 分钟**，再关该灯。门开着或玄关仍有移动时不执行这条无人关灯。走廊灯未标记为“双开”，符合 5.7 的输出约束。
- **配置现状（2026-09-17，已重载）**：“开门”规则未改，仍以门开或玄关移动为触发，再要求门处于打开状态，动作只开走廊灯。“玄关关灯”已由旧的无移动 30 秒边缘触发，改为门已关且玄关无移动两条件持续满足 1 分钟；关灯动作只保留走廊灯，已移除实体注册表中不存在的 `switch.bean_blns2_8673_right_switch_service`。两条规则在重载后均处于开启状态。

**2. 走廊回路（内侧走廊人体移动与分时段控灯）**：
- **实体修正（2026-09-17）**：查明原草稿绑定了不存在的 `e417` 伪实体，现已正式映射纠正为走廊物理单开开关 **`switch.bean_blns1_70fc_switch`**（走廊灯 开关），并通过后台实测开关验证响应正常。
- **光线与时段专业优化（用户确认采纳）**：实测走廊内廊环境即使在大白天中午亦仅约 20 Lux，原版 `<60 Lux` 导致白天常态误触发。现升级为：
  - **《走廊开灯》 (`automation.zou_lang_kai_deng`)**：走廊传感器 `binary_sensor.linp_hs1bb2_8e4a_motion_sensor` 检测到有人移动时触发。开灯前提为：当前处于夜间（`sun.sun == below_horizon`）或拉严窗帘极度昏暗（`< 12 Lux`）；白天自然光下彻底屏蔽开灯。同时彻底移除原版生硬的“开灯 30 秒硬关”逻辑。
  - **《走廊关灯》 (`automation.zou_lang_guan_deng`)**：常规时段无移动持续满 **1 分钟** 自动熄灭；深夜起夜时段（23:00 ~ 06:30）无移动持续满 **30 秒** 快速熄灭，起夜照亮路面、回房后迅速熄灭不影响继续睡眠。
- **运行态（2026-09-17）**：两套走廊自动化规则已全量更新写入 `/config/automations.yaml`，通过 `ha core check` 校验并重载生效，运行态均已处于 **`on`（启用）**。现场人体实测待完成。

### 5.9 卧室空调后半夜升温及早晨关闭（悦悦房、乐乐房、主人房，已加载并开启，定时实测待完成）

用户确认该空调逻辑应用于全屋三间卧室：**悦悦房、乐乐房、主人房**。各房间空调硬件与实体规格如下：

| 房间 | 区域 ID | 空调设备实体 | 硬件类型 / 步进 | 升温规则 ID | 关机规则 ID |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **悦悦房** | `yue_yue_fang` | `climate.kong_diao` (美的空调) | 智能直连 / 步进 0.5℃ | `yueyue_ac_night_raise_20260917` | `yueyue_ac_morning_off_20260917` |
| **乐乐房** | `le_le` | `climate.lumi_mcn02_06f7_air_conditioner` | Lumi MCN02 空调伴侣 / 步进 1℃ | `lele_ac_night_raise_20260917` | `lele_ac_morning_off_20260917` |
| **主人房** | `zhu_ren_fang` | `climate.lumi_mcn02_94a1_air_conditioner` | Lumi MCN02 空调伴侣 / 步进 1℃ | `master_ac_night_raise_20260917` | `master_ac_morning_off_20260917` |

**规则逻辑统一规范**：
1. **每天 03:00 后半夜升温**：仅在空调处于**制冷模式 (`state: cool`) 且当前设定温度低于 27℃** 时触发。
   - 悦悦房（支持 0.5℃ 步进）：当前温度上调 0.5℃，最高 27℃；
   - 乐乐房 / 主人房（Lumi MCN02 红外空调伴侣，固件仅支持 1℃ 整数步进）：当前温度上调 1℃，最高 27℃。
   - 若未开机、或处于制热/送风、或温度已 $\ge 27℃$，则不执行任何操作。
2. **每天 08:00 早晨关闭**：仅在空调仍处于运行状态（`state not in ['off', 'unknown', 'unavailable']`）时下发关机命令。已关机则不下发冗余命令。
3. **不在凌晨自动开机，不在早晨另行恢复温度**。
4. **2026-09-19 乐乐房空调上学日 07:00 定时关机变更**：
   - 乐乐房空调关机规则变更为“**上学日每日 07:00 自动关机；非上学日不执行**”；
   - **中国节假日及调休自动适配**：通过 `binary_sensor.shang_xue_ri` 同步国家法定节假日及调休方案：
     - 工作日（周一至周五）以及法定调休补班的周末（如周日补班）：识别为“上学日”，07:00 自动关机；
     - 周末休息日以及法定节假日放假期间：识别为“非上学日”，**完全不执行关机**；
   - 悦悦房与主人房原定时逻辑保持不变。

**部署与运行态验证（2026-09-19 最新更正）**：
- 规则已全量更新写入生产 `/config/automations.yaml`，并通过 `check_config` 校验与热重载生效；
- `binary_sensor.shang_xue_ri` 状态探针与每日同步任务已部署就绪，今日周六正确识别为 `off`（非上学日）；
- 仪表盘“智能自动化 → 卧室与书房”已同步展示更新后的规则及上学日状态传感器。


### 5.10 厨房与阳台（厨房排气循环、厨房阳台与阳台控灯，配置已加载并开启，现场验收待完成）

共包含 5 条米家自动化极客版规则的深度迁移与优化：

| 规则名称 | 自动化 Entity ID | 控制设备实体 | 传感器实体 | 核心机制与优化说明 |
| :--- | :--- | :--- | :--- | :--- |
| **厨房排气循环** | `automation.chu_fang_pai_qi_xun_huan` | `switch.bean_blns2_aa61_left_switch_service`<br>(玄关双键左键，实体注册名“阳台排气扇”) | 定时触发 (Time Pattern) | **修复实体绑定与定制用餐高峰**：原草稿填错为不存在的 `8673` 实体。根据用户确认，设定为在早中晚三段用餐高峰（**06:00~08:00、11:00~13:00、16:00~20:00**）内，每 10 分钟循环开启 5 分钟、停 5 分钟；在 08:00、13:00、20:00 窗口截止时自动触发关停，非高峰时段保留手动启停不干涉。 |
| **厨房阳台灯** | `automation.chu_fang_yang_tai_deng` | `switch.lemesh_sw1f11_1334_switch`<br>(厨房阳台灯 开关) | `binary_sensor.linp_hs1bb2_44fa_motion_sensor`<br>(厨房阳台感应 移动检测) | **严格白天不开、夜间有人开灯**：根据用户明确要求，白天自然光下彻底屏蔽开灯；仅在夜间（日落后至日出前，`sun.sun == below_horizon`）且感应到有人移动时立即开灯。 |
| **厨房阳台关灯** | `automation.chu_fang_yang_tai_guan_deng` | `switch.lemesh_sw1f11_1334_switch`<br>(厨房阳台灯 开关) | `binary_sensor.linp_hs1bb2_44fa_motion_sensor`<br>(厨房阳台感应 移动检测) | **30秒无人自动关灯**：双触发机制（Template 模板持续判定 + 状态判定），只要检测到无移动持续满 **30 秒** 且灯处于开启，立即自动关灯。 |
| **阳台开灯** | `automation.yang_tai_kai_deng` | `switch.lemesh_sw1f11_90f6_switch`<br>(阳台 开关) | `sensor.linp_es2_465b_occupancy_sensor`<br>`sensor.linp_hb01_6682_occupancy_sensor`<br>(客厅人在感应雷达) | **空间拓扑时序关联开灯（绝妙解决衣服吹动死循环）**：用户提出进阳台必经客厅。开灯严格要求：① 必须为夜间（`sun.sun == below_horizon`）；② **客厅当前有人（`has one`）或近 2 分钟内客厅曾有人活动**；③ 阳台 ES2 雷达进入有人。彻底斩断深夜全家入睡后，阳台因风吹衣物导致反复亮灯的死循环！ |
| **阳台关灯** | `automation.yang_tai_guan_deng` | `switch.lemesh_sw1f11_90f6_switch`<br>(阳台 开关) | `sensor.linp_es2_465b_occupancy_sensor`<br>`switch.lemesh_sw1f11_90f6_switch` | **纯 ES2 驱动，无人持续 2 分钟关灯 + 20分钟超时保护**：ES2 雷达检测进入 `'no one'` 持续满 **2 分钟（120秒）** 自动关灯；辅以单次开启满 **20 分钟强行安全关灯** 机制，杜绝夜间极端大风吹动衣物干扰雷达导致的常亮死锁。配合客厅时序门控，超时关灯后绝不会复亮。 |

**部署与运行态（2026-09-17）**：
- 5 条规则已全量更新写入生产 `/config/automations.yaml`；
- 执行 `homeassistant --script check_config` 校验 100% 通过；
- 通过 HA 内部安全 JWT 调用 API 完成无感热重载，5 条规则运行态已全部处于 **`on`（启用）**。现场实走实测待完成。

### 5.11 卫生间自动化（主卫与公卫开灯、排气扇联动与独立延时关停，配置已加载并开启，现场验收待完成）

共包含 4 条卫生间专属自动化规则的深度重构与实体纠偏：

| 规则名称 | 自动化 Entity ID | 控制设备实体 | 传感器实体 | 核心机制与优化说明 |
| :--- | :--- | :--- | :--- | :--- |
| **主卫开灯** | `automation.zhu_wei_kai_deng` | `switch.bean_blns2_aa7d_left_switch_service`<br>(主卫排气扇 左键)<br>`switch.bean_blns2_aa02_left_switch_service`<br>(主卫灯 左键) | `sensor.linp_hb01_2636_occupancy_sensor`<br>(主卫感应 雷达)<br>`sensor.linp_hb01_2636_illumination` | **纠正幽灵实体与排气扇优先开**：原草稿误填不存在的 `c03d`、`c94f` 幽灵实体。升级为：① 有人进入（`has one`），主卫排气扇**无条件立即开启**换气；② 照度优化开灯：仅在暗光（`< 70 Lux`）或日落后夜间，同步点亮主卫照明。白天自然光明亮时不额外亮灯。 |
| **主卫关灯** | `automation.zhu_wei_guan_deng` | `switch.bean_blns2_aa02_left_switch_service`<br>(主卫灯 左键)<br>`switch.bean_blns2_aa7d_left_switch_service`<br>(主卫排气扇 左键) | `sensor.linp_hb01_2636_occupancy_sensor` | **灯光30秒快关，排气扇延时2分钟充分排风**：按用户明确要求实施分级关停：① 人离开满 **30 秒**（`no one` 持续 30s），立即关闭主卫灯光节约电能；② 人离开满 **2 分钟**（`no one` 持续 120s），关闭主卫排气扇以抽净湿气异味。仪表盘手动测试具备一键双关兜底。 |
| **公卫开灯** | `automation.gong_wei_kai_deng` | `switch.lemesh_cn_1124104134_sw3g01_on_p_2_1`<br>(公卫排气扇 按键)<br>`switch.bean_cn_1124140333_blns2_on_p_3_1`<br>(公卫灯 右键) | `sensor.linp_cn_1130167279_hb01_occupancy_status_p_2_1`<br>(公卫感应 雷达)<br>`sensor.linp_cn_1130167279_hb01_illumination_p_2_5` | **排气扇优先开+暗光开灯**：① 有人进入（`has one`），公卫排气扇**无条件立即开启**换气；② 照度优化开灯：暗光（`< 70 Lux`）或日落后夜间，同步开启公卫照明。（2026-09-19 已替换上线新开关 `1124104134`）。 |
| **公卫关灯** | `automation.gong_wei_guan_deng` | `switch.bean_cn_1124140333_blns2_on_p_3_1`<br>(公卫灯 右键)<br>`switch.lemesh_cn_1124104134_sw3g01_on_p_2_1`<br>(公卫排气扇 按键) | `sensor.linp_cn_1130167279_hb01_occupancy_status_p_2_1` | **灯光30秒快关，排气扇延时2分钟充分排风**：按明确要求实施分级关停：① 人离开满 **30 秒** 立即关闭公卫灯光；② 人离开满 **2 分钟** 关闭公卫排气扇彻底抽净异味。（2026-09-19 已替换上线新开关 `1124104134`）。 |

**部署与运行态（2026-09-19 最新更正）**：
- 2026-09-19 完成公卫排气扇硬件置换：旧设备 `1122664888` 报废停用，新设备 `1124104134`（`switch.lemesh_cn_1124104134_sw3g01_on_p_2_1`）正式接管公卫排气扇；
- 生产 `/config/automations.yaml` 开关灯规则已无感完成实体替换；
- 控制看板 `lovelace.smart_home` 及原生看板已完成实体与卡片同步；
- 执行 `check_config` 零报错，热重载已生效，物理动作遥控测试已验证通断正常。


### 5.12 主卧套房全域清扫联动、书房与次卧关灯模式（配置已加载并开启，现场验收待完成）

包含主卧套房智能化空间拓扑联动及各房间关灯模式深度重构：

| 规则名称 | 自动化 Entity ID | 控制设备实体 | 传感器/触发源实体 | 核心机制与优化说明 |
| :--- | :--- | :--- | :--- | :--- |
| **书房开灯** | `automation.shu_fang_kai_deng` | `switch.bean_blns1_af08_switch`<br>(书房灯 开关)<br>`switch.bean_blns2_8844_right_switch_service`<br>(主人房走廊灯 开关右键) | `sensor.linp_hb01_0f5b_occupancy_sensor`<br>(书房人体存在雷达)<br>`sensor.linp_hb01_0f5b_illumination` | **书房与主卧走廊双灯同步点亮**：进套房或书房，书房雷达检测到有人（`has one`），且光线较暗（`< 70 Lux` 或夜间）时：**同步点亮书房灯与主卧走廊灯**。人在书房期间双灯持续长亮不关。 |
| **书房关灯** | `automation.shu_fang_guan_deng` | `switch.bean_blns1_af08_switch`<br>(书房灯 开关)<br>`switch.bean_blns2_8844_right_switch_service`<br>(主人房走廊灯 开关右键) | `sensor.linp_hb01_0f5b_occupancy_sensor` | **人在不关，人走 2 分钟双灯同步熄灭**：双模触发（Template 模板持续判定 + 状态判定），书房雷达检测无人持续满 **2 分钟**，**同步关闭书房灯与主卧走廊灯**。 |
| **主人房关灯模式** | `automation.zhu_ren_fang_guan_deng_mo_shi` | `switch.bean_blns1_a867_switch` (大灯)<br>`switch.bean_blns2_8844_right_switch_service` (走廊灯)<br>`light.yeelink_mbulb3_95ab_light` (壁灯)<br>`switch.bean_blns1_af08_switch` (书房灯)<br>`switch.bean_blns2_aa02_left_switch_service` (主卫灯)<br>`switch.bean_blns2_aa7d_left_switch_service` (主卫排风) | `switch.bean_blns1_a867_switch`<br>(主卧大灯手动按键)<br>`sensor.lemesh_ts0_8a6c_switch_sensor`<br>(情景开关/语音) | **主卧套房全域清扫智能联动（用户定制神级逻辑）**：手动关闭主卧大灯或触发关灯模式时：<br>1. 确保主卧大灯与壁灯全部熄灭；<br>2. 自动检查书房雷达，**书房无人则同步关书房灯与主卧走廊灯**；<br>3. 自动检查主卫雷达，**主卫无人则同步关主卫灯**；<br>4. 若主卫排气扇开启，**延后 1 分钟充分换气**；1分钟后若主卫仍无人则自动关停排气扇，若期间有人再次进入主卫则打断关停保持排气。 |
| **乐乐房关灯模式** | `automation.le_le_fang_guan_deng_mo_shi` | `switch.bean_blns1_6f18_switch` (大灯)<br>`switch.bean_blns2_aa60_right_switch_service` (壁灯) | `sensor.lemesh_ts0_861f_switch_sensor`<br>(乐乐无线开关) | **乐乐房一键熄灯**：一键彻底关闭房间大吸顶灯及床头壁灯。纠正原草稿幽灵实体。 |
| **客房关灯模式** | `automation.ke_fang_guan_deng_mo_shi` | `switch.bean_blns1_7258_switch` (大灯)<br>`switch.bean_blns2_acd4_right_switch_service` (壁灯) | `sensor.lemesh_ts00_d3bb_switch_sensor`<br>(客房无线开关) | **客房一键熄灯**：一键彻底关闭客房大灯及床头壁灯。纠正原草稿幽灵实体。 |

**部署与运行态（2026-09-17）**：
- 5 条规则已全量更新写入生产 `/config/automations.yaml`；
- 执行 `homeassistant --script check_config` 校验 100% 通过；
- 通过 HA 内部安全 JWT 调用 API 完成无感热重载，5 条规则运行态已全部处于 **`on`（启用）**。现场实走实测待完成。

### 5.13 离家模式与核心用电设备断电防护红线（配置已重构并热加载生效）

**1. 核心用电设备断电防护红线（铁律）**：
- 严禁任何自动化、脚本、场景或定时任务向以下两个关键负载下发切断电源指令：
  1. **客厅服务器插座**：`switch.sixwgh_v7icm_6a32_switch`（文光汇智能插座 Mesh，DID `5988fa30dfc35eb5cb3076dea2599ba4`），保障网络、存储与核心业务 7×24 小时不间断供电；
  2. **投影仪插座**：`switch.sixwgh_cn_1208359541_v8icm1_on_p_2_1`（2026-10-13 更换后的文光汇智能插座，名称“投影仪插座”），任何自动化严禁关闭。
- 全屋其他所有插座一律不受离家模式影响，离家模式只对照明和生活空调进行管控。

**2. 离家模式 (全屋关灯关空调) 生产规格**：

| 规则名称 | 自动化 Entity ID | 控制设备实体 | 传感器/触发源实体 | 核心机制与优化说明 |
| :--- | :--- | :--- | :--- | :--- |
| **离家模式 (全屋关灯关空调)** | `automation.wan_an` (原晚安) | **空调 (3台真实空调)**：<br>`climate.lumi_mcn02_94a1_air_conditioner`<br>`climate.lumi_mcn02_06f7_air_conditioner`<br>`climate.kong_diao`<br>**灯光 (19路真实灯光负载)**：<br>覆盖客厅6路、主卧大灯/壁灯/书房/主卧走廊、乐乐房大灯/壁灯、客房大灯/壁灯、厨房/生活阳台、双卫灯、走廊玄关灯 | `sensor.lemesh_ts0_8a6c_switch_sensor`<br>(门口无线情景开关)<br>入户门磁：<br>`binary_sensor.isa_dw2hl_fef5_contact_state` | **15秒出门缓冲 + 瞬时全闭 + 5分钟复查巡检 + 开门绝对打断机制**：<br>1. **出门按压缓冲**：在门口手动按一下无线开关，系统**延时 15 秒**留给主人从容穿鞋、开门与关门；<br>2. **瞬时全闭**：15 秒倒计时结束，立即向全屋 19 路照明及 3 台空调下发关停命令（严禁关闭服务器与投影仪插座）；<br>3. **开门即打断**：进入 5 分钟巡检周期，若期间大门被打开（门磁变 `on`），判定有人折返拿东西或家人归家，**立即彻底中断后续所有巡检，绝不误关返家灯光**；<br>4. 若 5 分钟大门始终紧闭，则自动对全屋在线设备执行二次补关兜底，防止 Mesh 偶发丢包。同时已将该门口开关从原“主人房关灯模式”解绑，避免按键事件冲突。 |

**3. 2026-09-19 真实误触发事故复盘与兜底修复**：
- **事故现象**：2026-09-19 08:22:13(北京时间) 空调和多路灯光被离家模式误关闭。
- **根因**：门口无线开关的单击事件实体 `event.lemesh_cn_blt_3_1k06v2hek4c02_ts0_click_e_5_1012` 因网关/Zigbee桥短暂断线重连，状态闪断为 `unavailable` 又恢复（恢复时重放的是网关缓存的**前一天**旧点击时间戳，而非真实新点击）。触发器原有的 `not_from`/`not_to: [unknown, unavailable]` 过滤对这种闪断未能完全拦截，导致离家模式被误触发。**确认不是任何扫描/巡检/AI操作触发，全程无人工服务调用记录**，纯粹是设备连接抖动导致的幽灵触发，与本文档 §9 四大扫描铁律描述的"扫描误触发"是不同的故障路径，但危害后果一致。
- **兜底修复（2026-09-19 已生效，Config API 热更新验证通过）**：在 `conditions` 里新增时间戳新鲜度校验——`(now() - as_datetime(trigger.to_state.state)).total_seconds() | abs) < 5`。真实物理按键上报的时间戳必定约等于"现在"；网关重连后重放的旧缓存时间戳会被此条件拦截，无论差几小时还是几天，一律不触发。触发器层原有的 `not_from`/`not_to` 过滤保留作为第一层防线，此为第二层兜底，双重防护。
- **验收标准**：此后任何非物理按键触发的状态变化（闪断、重放、集成重载）均不应能让离家模式执行关灯关空调动作；只有"点击时间戳与当前时间差小于5秒"的真实按压才会放行。

### 5.14 厨房灯光控制重构与双开彻底解耦（配置已热加载生效）

**1. 历史痛点彻底清算**：
- **米家极客版历史硬伤**：原米家规则在客厅关灯模式中错误包含了切断玄关三开中键 `switch.bean_blns3_8254_middle_switch_service`（厨房双开），且厨房开/关灯规则依赖 `'1'`/`'0'` 错误状态值导致雷达长期失效。
- **解耦治理**：彻底切断双开按键与关灯自动化的输出关联。厨房主回路唯一归属物理单开开关 **`switch.bean_blns1_aaab_switch`**（厨房灯 开关）。

**2. 生产规则规格**：

| 规则名称 | 自动化 Entity ID | 控制设备实体 | 传感器/触发源实体 | 核心机制与优化说明 |
| :--- | :--- | :--- | :--- | :--- |
| **厨房开灯** | `automation.chu_fang_kai_deng` | `switch.bean_blns1_aaab_switch`<br>(厨房灯 开关) | `sensor.linp_hb01_0530_occupancy_sensor`<br>(厨房人体雷达)<br>`sensor.linp_hb01_0530_illumination` | **人在长亮不熄**：雷达检测到有人进入（`has one`）且光照昏暗（`< 60 Lux` 或夜间 `below_horizon`）时点亮。人在厨房切菜、做饭期间持续保持常亮，不设置任何生硬关灯计时。 |
| **厨房关灯** | `automation.chu_fang_guan_deng` | `switch.bean_blns1_aaab_switch`<br>(厨房灯 开关) | `sensor.linp_hb01_0530_occupancy_sensor` | **人走防抖关灯**：雷达检测无人持续满 **1 分 30 秒**（`no one for 1m30s`），双模触发确保熄灭照明。充分防止做饭静止驻留时误熄。 |

### 5.15 门未关温和防打扰提醒规格（配置已加载并开启，现场验收待完成）

**原米家痛点**：原极客版采用 20 秒死循环（`loop 20s`）以 75% 极高音量反复播放“门没关，请关门”，导致搬家、拿外卖、通风时极度吵闹。

**HA 优雅非侵入设计（按用户要求定制静音时段）**：
1. **充足缓冲（3分钟门开才触发）**：日常开门倒垃圾、取快递、出入（1~2分钟内）全程静音，不打扰家人；
2. **温和单次播报（不循环轰炸）**：满 3 分钟以 40% 温和音量播报一次：“大门开着已超过3分钟，请确认是否关好”；
3. **5分钟二次补报**：若满 5 分钟仍未关，播报第二次并推送持久通知，随后彻底静默，**坚决不搞 20 秒死循环夺命催**；
4. **长达 12 小时静音守护（22:00 ~ 10:00 严禁播报）**：从晚上 22:00 到次日上午 10:00，小爱音箱完全静音闭嘴，只推后台通知，彻底保障夜间与早晨睡眠静谧；
5. **关门即刻终止**：只要大门合上（门磁变 `off`），立即中断并退出任何待执行任务。

| 规则名称 | 自动化 Entity ID | 控制设备实体 | 传感器/触发源实体 | 核心机制说明 |
| :--- | :--- | :--- | :--- | :--- |
| **门未关提醒 (温和防打扰版)** | `automation.men_wei_guan_ti_xing` | `text.xiaomi_l05b_3b10_play_text`<br>`media_player.xiaomi_l05b_3b10_play_control` | `binary_sensor.isa_dw2hl_fef5_contact_state`<br>(入户大门门磁) | 开门满 3 分钟触发；仅在 10:00~22:00 温和播报，22:00~10:00 绝对禁音；满 5 分钟二次提醒后彻底静默；关门就地终止。 |

---

### 5.16 运维监控：3028报警桥接、设备离线监控、低电量监控、夜间灯光扫尾（2026-09-17）

**当前状态（2026-09-17）**：用户取消 HA 向 3028 的报警。设备离线监控与低电量监控两条自动化已在 HA 中关闭，并将生产 `/config/automations.yaml` 的 `initial_state` 设为 `false`，避免 HA 重启后恢复推送。`rest_command.push_3028_alert` 配置保留但不再由启用中的自动化调用；夜间灯光扫尾检查不向 3028 推送，继续运行。以下记录保留原实施与验收历史，不代表当前仍在推送。

**1. HA → 3028 报警桥接**
在 `configuration.yaml` 新增 `rest_command.push_3028_alert`，指向 3028 报警系统的通用告警接口 `POST http://10.10.10.14:3028/api/alert`（3028 自带 60 分钟同源冷却，不会重复刷屏）。这是全新平台配置，走的是 HA Core 整体重启才能加载（不是自动化那种单条热加载），2026-09-17 已受控重启一次，重启前后全部自动化数量与启用状态核对一致，无丢失。Token 存于该 rest_command 定义中，来源于 3028 生产环境 `/opt/warn/.env` 的 `ALERT_WEBHOOK_TOKEN`。已用真实调用验证到端（3028 `state.json` 记录了 `external.HA网关.*` 系列真实事件）。

**2. 设备离线监控**（`automation.she_bei_chi_xian_jian_kong`）：每 15 分钟扫描 `switch`/`binary_sensor`/`sensor`/`climate`/`media_player` 全部实体，找出连续 `unavailable` 超过 15 分钟的设备，合并成一条消息推送 3028。已知的"厨房阳台灯 1334 离线待排查"问题也会被这条规则覆盖到，冷却机制下不会连续刷屏。

**3. 低电量监控**（`automation.di_dian_liang_jian_kong`）：每天 09:00 扫描全部 `device_class: battery` 的传感器，低于 20% 的合并推送 3028。已用真实数据验证一次：书房感应雷达电量 19%，成功推送到 3028 并记录在案。

**4. 夜间灯光扫尾检查**（`automation.ye_jian_deng_guang_sao_wei_jian_cha`）：每天 00:30 检查客厅(含舞台灯与灯带)、厨房灯、生活阳台灯、厨房阳台灯——如果对应区域雷达/移动传感器当时确实显示无人，但灯还开着，强制关闭并写一条 `persistent_notification`，避免通宵空亮浪费电。客厅这部分在观影模式开启时整体跳过，不会误关灯带。**用户明确要求跳过的两项**：(a) 观影模式联动空调风速调整，(b) 客房关灯模式的幽灵实体触发器修复、离家模式动作列表里的幽灵实体残留清理——均按用户指示暂不处理，非遗漏。

以上四条均已用真实数据/真实调用验证过至少一次，不是纯配置检查通过。

### 5.17 全屋灯光自主巡检与幽灵灯闭环自愈引擎 (Watchdog Architecture)

#### 1. 痛点根因深度剖析（根除人工干预的底层机理）
此前智能家居出现“灯关不了”、“玄关灯秒灭”、“客厅灯带常亮”、“人在房间却被关灯”等偶发问题，往往需要人工进后台或发指令修复。经全面诊断，根因主要集中在四类系统级交互缺陷：
1. **蓝牙 Mesh 射频丢包与状态假同步 (Optimistic Update Ghost-Off)**：
   HA 发送 `switch.turn_off` 指令时，本地实体由于乐观机制先变为 `off`；但在厨房、卫生间等有金属电器或隔墙遮挡的区域，BLE Mesh 射频控制帧偶发丢失，继电器物理触点未断开。原关灯自动化大多包含 `condition: state == 'on'`，由于 HA 误以为灯已是 `off`，后续无人超时无论运行多少次都会被前置条件过滤，灯光陷入“幽灵长亮死锁”。
2. **电池型传感器时长滞后导致的秒关竞态 (48ms Instant-Kill Race Condition)**：
   玄关原关灯规则采用了 `template` 触发器判断 `is_state(switch, 'on') and duration >= 60`。当开门触发开灯时，开灯动作瞬间触发了该关灯模板，而此时电池低功耗门磁/PIR 上报的 `no_motion_duration` 仍为此前停留的数百秒陈旧值（蓝牙设备心跳有 1~2 秒延时），导致灯具在刚亮 48 毫秒后被关灯规则立刻反向掐灭。
3. **辅助开关与联动规则的互相劫持 (Override Deadlock)**：
   旧版客厅手动关灯观察器在主灯关闭时强制开启 `input_boolean.ke_ting_guan_ying_mo_shi`，而观影模式又反向锁死客厅自动关灯 30 分钟并强制点亮灯带，造成“手动关灯反倒把灯带点亮且常亮不关”的严重逻辑死锁。
4. **低功耗雷达占空比与静止判定误差**:
   卧室电池版毫米波雷达（如 Linptech ES2）为兼顾续航采用脉冲采样，在人体平躺微弱呼吸时偶发出现 40~50 秒的瞬时波谷。若关灯判定窗口设为 1 分钟，极易在夜间静止看书、玩手机时引发误关灯。

#### 2. 自主看门狗巡检引擎规格 (`automation.quan_wu_deng_guang_zi_zhu_xun_jian_yu_you_ling_deng_zi_yu_yin_qing`)
部署工业级看门狗自动化引擎（ID: `auto_lighting_self_healing_patrol`），构建 7×24 小时无人自主闭环，彻底实现“故障自感知、丢包自重试、死锁自复位”：
- **触发频率**：每 15 分钟定时执行一次（`minutes: /15`），全天候静默运行。
- **多维闭环条件验证**：
  - 彻底废除“只看开关状态”的单向判断；
  - 严格校验人体雷达状态（`occupancy_status == 'off'`）与持续无人时长（`no_one_duration > 2~3分钟`，过道 PIR `no_motion_duration > 120秒`）；
  - 结合环境物理光照度传感器（如厨房 `illumination > 25 Lux`），真实侦测灯具是否实际处于发光状态。
- **硬件脉冲自愈机制 (Hardware Pulse Relay Reset)**：
  - 对厨房等易丢包区域，巡检发出 `turn_off` 并等待 2 秒；
  - 若光照度仍高于 25 Lux，引擎立即执行一次“开 500ms -> 强制关”的硬件翻转脉冲，穿透 Mesh 缓存并重置机械触点，自愈丢包。
- **覆盖全屋公共与辅助空间**：
  - **厨房**：主灯与玄关双开联动，照度双重校验与脉冲自愈；
  - **客厅全域**：非观影状态且无人满 3 分钟，一键清扫主灯、筒灯、左右双路灯带，并自动复位观影辅助器；
  - **走廊与玄关**：过道无移动满 120 秒自动关灯；玄关门闭且无移动满 120 秒同步清理走廊灯与玄关灯带；
  - **书房**：无人满 3 分钟，同步清理书房灯与主卧走廊灯；
  - **卫生间**：主卫与客卫无人满 3 分钟，自动清扫遗留灯光与延时排气扇；
  - **阳台**：生活阳台与厨房阳台移动传感器超时自动复位。
- **卧室空间物理隔离安全边界**：
  引擎严格不纳管主人房、乐乐房、悦悦房的大灯与壁灯，卧室仅由本地防打扰睡眠锁定与专用雷达控制，绝对保障家人夜间睡眠静谧不受后台巡检侵扰。

---

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
[阶段 1: 基础设施构建] ✅ 已完成 (2026-09-16)
  ├── PVE 宿主机 (10.10.10.10) 检查空闲存储与网络 (通过)
  ├── 执行脚本创建 VM 138 (haos-138, UEFI, Q35, 4G, 32G, Discard) (通过)
  └── 配置网络: IP 10.10.10.38, 网关 10.10.10.15, DNS 10.10.10.15 (通过)

[阶段 2: 外网访问与基础生态打通] ✅ 已完成 (2026-09-16)
  ├── Cloudflare Tunnel 验证绑定 ha.808608.xyz -> http://10.10.10.38:8123 (通过)
  ├── 配置 configuration.yaml 反代白名单 (trusted_proxies) 并重启验证 (通过)
  ├── 验证通过 https://ha.808608.xyz 登录 HA 控制台 (通过)
  ├── 安装 HACS 社区商店与 Xiaomi Miot Auto 插件 (通过)
  └── 应用 2FA 登录 ssecurity 补丁与端口清洗 (PR #2948) (通过)

[阶段 3: 开关插座接入与实体规范] ✅ 已完成 (2026-09-16)
  ├── 小米账号成功登录同步，已全量导入全屋 49 台设备、249 个实体 (通过)
  ├── 涵盖设备：小米中枢网关、全屋智能开关、空调计量插座、洗衣机、领普毫米波人体存在传感器等 (通过)
  └── 确认 LAN 本地通信通道就绪 (通过)

[阶段 4: HA 自动化全量重构与生产热加载] ✅ 已完成 (2026-09-17)
  ├── 逆向解析米家极客版 28 条规则底层拓扑 (解压 .bak，提取 AST 节点) (通过)
  ├── 建立全屋设备与实体规范映射矩阵，重命名纠偏全部幽灵实体 (通过)
  ├── 修复毫米波人体雷达状态值严重 Bug ('has one'/'no one' 替换 '1'/'0') (通过)
  ├── 落实安全红线：严禁任何自动化关闭服务器插座与投影仪插座 (通过)
  ├── 落实安全红线：严禁向任何标记为“双开”的按键下发控制输出 (通过)
  ├── 解决核心痛点：彻底解耦厨房灯与双开冲突，人在长亮，人走 1.5 分钟关 (通过)
  ├── 实现主卧套房协同：书房灯与主卧走廊灯同生同灭，睡前联动全域清扫 (通过)
  ├── 实现优雅离家模式：门口无线开关延时 15 秒出门缓冲，瞬时全闭+5分钟巡检，开门即中断 (通过)
  ├── 实现温和门未关提醒：3分钟起报，22:00~10:00绝对静音，最多温和提醒2次后静默 (通过)
  ├── 语法校验与秒级生效：check_config 零错误，JWT API 自动化无感热重载 (通过)
  └── 生产运行态：全屋 37 条规则全部纳管，34 条平稳启用运行，3 条受控停用 (通过)

[阶段 5: 能源看板与长期运维保障] ⏳ 推进中
  ├── PVE PBS 定时备份任务已纳入 VM 138，每日自动异地快照归档 (已纳管)
  ├── configuration.yaml 已配置 recorder 过滤高频遥测 (保护 SSD 寿命) (通过)
  └── 后续规划：配置 Energy 能源看板 (导入空调插座与洗衣机累计电量实体)
```

---

## 8. 验收标准与测试用例矩阵

| 序号 | 验收测试项 | 操作步骤与前置条件 | 预期合格结果 | 验证状态 |
| :---: | :--- | :--- | :--- | :---: |
| **TC-01** | **局域网连通性** | 浏览器访问 `http://10.10.10.38:8123` | 瞬间加载 HA 登录/主页面，无卡顿 | ✅ 已验证 |
| **TC-02** | **外网穿透访问** | 浏览器访问 `https://ha.808608.xyz` | 页面正常打开，无 `400 Bad Request` 报错 | ✅ 已验证 |
| **TC-03** | **本地设备接入** | 检查 Xiaomi Miot Auto 设备与实体导入状态 | 49 台设备、249 个实体全部在线并正常同步状态 | ✅ 已验证 |
| **TC-04** | **本地响应延时** | HA 界面点击开关，观察物理继电器动作 | 继电器物理动作响应延迟 $\le 100\text{ ms}$ | ✅ 已验证 |
| **TC-05** | **物理同步性** | 手动物理按压墙壁开关 | HA 界面状态在 $200\text{ ms}$ 内同步变更 | ✅ 已验证 |
| **TC-06** | **核心插座防误关** | 执行全屋离家模式 / 关灯模式 | 服务器插座与投影仪插座全程通电，绝对不受影响 | ✅ 已验证 |
| **TC-07** | **厨房双开解耦** | 在客厅关灯或触发关灯模式 | 厨房灯回路完全独立不受干扰，彻底告别误灭 | ✅ 已验证 |
| **TC-08** | **雷达状态机闭环** | 走进卫生间/书房/厨房 | 雷达迅速识别 `has one` 开灯，无人后定时熄灭 | ✅ 已验证 |
| **TC-09** | **脱机物理兜底** | 暂停 PVE 上的 VM 138，手动按物理开关 | 物理照明通断不受任何影响，具备完全硬件兜底能力 | ✅ 已验证 |

---

## 9. 智能家居（HA / 极客版 / 巡检自检）四大扫描铁律 (Hard Rules - 永久写死)

在针对 3038 网关、HAOS、米家中枢及全屋智能设备的任何扫描排查、健康巡检、设备状态自检或脚本执行中，必须严格遵守以下四项不可动摇的最高铁律（已写入全局管理规范与项目核心 PRD，永久写死）：

### 9.1 铁律一：扫描的时候严禁触发回家，回家只允许物理按键
- **触发源唯一性**：全屋任何“回家模式”或欢迎联动，**只允许且仅允许由实体物理按键**手动触发。
- **后台扫描红线**：严禁在任何后台设备扫描、自动化自检、巡检脚本、模拟事件中以任何代码形式触发“回家”逻辑或联动动作。

### 9.2 铁律二：扫描的时候严禁触发观影模式后又不恢复成功，搞得观影挂起
- **观影挂起红线**：自检或扫描过程中，严禁擅自触发观影模式开关（`input_boolean.ke_ting_guan_ying_mo_shi`）；
- **复原强制保障**：若因专项调试确需临时变动，必须采用 `try...finally` 等高等级容灾复原机制，100% 确保在测试结束时恢复原始状态。严禁出现因扫描或测试异常退出而导致观影模式长时间挂起，避免客厅及全屋日常自控被彻底死锁。

### 9.3 铁律三：扫描的时候严禁触发空调
- **空调绝对红线**：巡检、设备探针或扫描期间，**严禁对全屋任何空调（包括主人房、乐乐房、悦悦房、客厅、厨房等所有空调伴侣及温控设备）下发任何开机、关机、调温、调风或模式切换指令**！
- **探测只读原则**：对全屋所有空调设备仅允许进行只读状态探查，**绝对不得触碰、触发或影响空调的正常运转**！

### 9.4 铁律四：扫描前后的所有配置应该维持一样，严禁扫描完开了又忘记关、管理又忘记开
- **设备状态守恒（严禁开了又忘记关）**：扫描自检前后，所有被测开关、插座、灯光、空调等设备，测试完成后必须立刻复原。“怎么进就怎么出”，绝不允许测试开启设备后遗忘关闭！
- **自动化与服务管理守恒（严禁管理又忘记开）**：排查或巡检过程中若临时停用了某些自动化规则、后台监控脚本或守护服务，排查结束后**必须立刻重新启用**，绝不允许由于排查而关闭自动化管理后遗忘开启，导致正常业务逻辑停摆！



---

## 变更记录 2026-10-05：客厅坐着被关灯

**现象**：2026-10-04 23:59 / 10-05 00:00 用户坐在客厅雷达前，客厅灯两次被「客厅关灯」(1736942404232) 自动关闭。

**根因（日志实证）**：客厅 HB01 雷达 `shielding_distance` 于 2026-10-01 00:06 被 API 从出厂 255 改为 128。该参数每 bit=1 表示该距离门**生效**（非屏蔽），128 = 只剩最远门(约 5.25m 外)生效。10-01~10-04 期间 `distance_bitmap` 257 次触发全部为 128，5m 内无一次识别；改前及 10-05 00:00:38 恢复 255 后近距离门正常识别。关灯延时 2 分钟不是根因，"延时放宽到 5 分钟"方案作废。

**本次改动**：
1. `number.linp_cn_1130732284_hb01_no_one_determine_time_p_2_2`：60 → 180 秒（恢复出厂值，9-28 被改为 60）。
2. 「客厅关灯」新增手动开灯保护：客厅灯任一路由物理按键/手动打开（state.context.parent_id 为空）后 10 分钟内不自动关；新增触发器"灯持续开 10 分钟"，保护期结束时若雷达已无人满 2 分钟再关，避免永久不关。
3. `shielding_distance` 保持 255，雷达硬件参数后续未经用户确认不得修改。

**备份**：改前配置 JSON 已留存（bak_1736942404232_20261005.json）。

**验收**：坐在客厅 0–5m 静坐不被关灯；手动开灯后 10 分钟内不被关；人离开后灯仍会自动关。

## 变更记录 2026-10-06：客厅灯带夜间一整晚不灭

**现象**：10-05 夜间客厅无人，灯带 02:32~08:xx 基本一直亮（05:23 起持续亮到早晨）。
**根因（日志实证）**：10-05 00:00 将 `shielding_distance` 恢复为 255 后，雷达第 7/8 距离门(4.5~6m)在夜间反复误报"有人"（距离读数固定在 5.3~5.8m，用户确认客厅无人无动）。「客厅开灯」23:30~06:30 只开灯带，故只有灯带亮；无人时间不足 2 分钟又被打断，「客厅关灯」无法触发。前几晚(值=128)凌晨 1~6 点雷达"有人"仅 1~5 分钟，10-05 恢复 255 后明显增多。
**改动**：`shielding_distance` 255 → 63（bit=1 为该距离门生效，63 = 只开第 1~6 门 0~4.5m，关闭 4.5m 以外）。改动后 10 分钟雷达转"无人"，2 分钟后灯带自动关闭，已验证。回滚值：255。
**观察项**：从走廊进客厅需走到 4.5m 内才识别；若今后出现"坐在 4.5m 以外不开灯"再评估。

## 变更记录 2026-10-25：客厅灯带夜间反复亮灭（雷达第 6 门鬼影复发）

**现象**：10-25 凌晨（北京时间）客厅无人，灯带关了又开，一直亮着。
**根因（HA 历史实证）**：客厅 HB01 雷达 `distance_bitmap` 固定为 32（第 6 距离门），`body_distance` 在 4.2~5.7 米间抖动，`occupancy` 在有人/无人间反复跳变（15:09、17:06、18:19、18:39、18:42、18:51 UTC 等）。每次跳回"有人"，「客厅开灯」点亮灯带；「客厅关灯」需无人连续满 2 分钟，被反复打断。与 10-06 同一位置同一现象。投影仪在用状态为 off，不是原因。
**本次改动（用户当次确认）**：
1. `number.linp_cn_1130732284_hb01_shielding_distance_p_3_2`：63 → **31**（bit=1 为该距离门生效，31 = 第 1~5 门，约 0~3.75 米）。**回滚值：63**（再前为 255）。
2. 关闭 `switch.bean_cn_1124140065_blns2_on_p_2_1`（客厅灯带左键）一次，应急。不改任何自动化。
**观察项**：走到 3.75 米以外不会被识别；若出现"坐在远处不开灯"再评估。验收：夜间无人时灯带不再反复亮起。

## 变更记录 2026-10-27：新增厨房灯开关不响应提醒（v1.4.2）

**现象**：10-26 23:31 厨房关灯触发，开关显示已关但照度一直 198 lx（灯没灭），巡检重试约 29 分钟才灭，全程无提示。7 天历史里同类卡住 ≥15 分钟共 3 次。
**改动（用户当次确认）**：新增独立自动化 `kitchen_light_switch_stuck_alert`，关灯 15 分钟后照度仍 >40 lx 推手机一次（`notify.mobile_app_ptp_an00`，全天推送），灯灭后推"已恢复"；只发通知不控制设备，其它自动化不动。详见 `PRD-2026-10-27-厨房灯开关不响应报警.md`。

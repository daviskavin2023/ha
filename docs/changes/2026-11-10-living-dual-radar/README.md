# 客厅USB LD2410与HB01融合（2026-11-10）

用户要求：已接上的USB感应与现有客厅人在联动。旧BLE接收不稳定；原客厅消费者只看HB01，新增雷达并未参与保灯。USB原二值模板还会在原始数据异常时默认false，不能直接把它当作可靠无人。

## 生效规则

- 原有HB01：`binary_sensor.linp_cn_1130732284_hb01_occupancy_status_p_2_1`。
- USB显示实体：`binary_sensor.ke_ting_usblei_da_you_ren`。融合直接校验原始`sensor.ld2410_usb_json`的occupancy布尔值及last_reported，避免无效数据默认false。
- 汇总：`binary_sensor.ke_ting_shuang_lei_da_you_ren`。任一有效源on即on；两路都有效且off才off；其余unavailable。USB报文超20秒视为无效，每5秒复核，因此超时显现最多约25秒。
- 常规客厅关灯、巡检、夜间扫尾：汇总off持续至少120秒；主关灯每30秒复核，避免重载丢失for计时后永久不关灯。设备自身无人延时仍在，120秒从汇总off开始计算。
- 开灯保持原暗光、观影、投影、会客/生日和夜间分支。HB01接近事件仅接受5秒内新事件。数据恢复on不通过off→on主开灯触发。
- 舞台灯未知时阻止默认关闭分支；会客无人退出保留5分钟+5分钟；风扇保留原温度/场景条件，干扰关机额外要求USB有效且无人。并未解除原有灯关风扇绑定，也未重新设计全屋模式。
- 13条自动化逐ID保存/重载；原禁用的手动关灯观察自动化保持禁用。具体ID及逐项原始备份见apply-summary.json及before-*.json。

## 验证与实际验收边界

12项HA纯模板矩阵涵盖任一有人、双无人、单路掉线、USB陈旧、类型错误及未来时间；check_config有效；13条生产保存后回读一致；自动化启停状态无变化。未调用automation.trigger、未模拟状态，未执行灯/风扇/空调/回家/离家服务，未改雷达底层参数。

软件接入与逻辑已验证；未凭配置声称沙发静坐覆盖、东窗帘/风扇误报已解决。下一步实际使用验收：沙发静坐不误灭、离开后双路转无人再关灯、风扇及窗帘扰动无持续占用。若任一路误报持续on，融合会保灯，需依原始距离/能量及时间记录判断，不能用缩距离盲改硬件。

## 备份与回滚

- HA模板前原配置：HAOS`/config/backups/living-dual-radar-20261110/configuration.yaml.before`（含原有私密配置，仅留主机）。不要整份覆盖当前配置；对比后只移除本次unique_id=living_room_dual_radar_occupancy模板块，避免覆盖并行改动。
- 自动化逐条原定义：本目录before-<id>.json；回滚前与当前版本核对并发修改，逐ID恢复并回读。未变更的禁用观察规则不需恢复。
- 仅在自动化引用恢复完成后移除融合模板并重载template；同步本地exports及USB绑定记录。历史原设备/实体未删除。

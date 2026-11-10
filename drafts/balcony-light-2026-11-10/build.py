#!/usr/bin/env python3
"""从 live/ 生成 new/ 下三条自动化（只改阳台相关），不接触 HA。"""
import json, copy
LIGHT = "switch.lemesh_cn_888711197_sw1f11_on_p_2_1"
S04 = "event.linp_cn_blt_3_1k0m2afv4cg01_hs1bb2_motion_detected_e_2_1008"
S04_NOMO = "sensor.linp_cn_blt_3_1k0m2afv4cg01_hs1bb2_no_motion_duration_p_2_1024"
S04_LUX = "sensor.linp_cn_blt_3_1k0m2afv4cg01_hs1bb2_illumination_p_2_1005"
NEAR = "sensor.ke_ting_lei_da_jin_chu_zou_dong_shi_jian"
LATCH = "input_boolean.yang_tai_you_ren"
DUAL = "binary_sensor.ke_ting_shuang_lei_da_you_ren"
JSON = "sensor.ld2410_usb_json"
FRESH = ("{% set j = states." + JSON + " %}"
         "{% set fresh = j is not none and j.state not in ['unavailable','unknown'] "
         "and (now() - j.last_reported).total_seconds() <= 60 %}")
REF = ("{% set e = states('" + S04 + "') %}"
       "{% set s04 = as_datetime(e) if e not in ['unknown','unavailable'] else none %}"
       "{% set ref = [s04, states." + LIGHT + ".last_changed] | reject('none') | max %}")
def idle(sec, latched):
    return (REF + "{{ is_state('" + LIGHT + "','on') and is_state('" + LATCH + "','" + ("on" if latched else "off") +
            "') and (now() - ref).total_seconds() >= " + str(sec) + " }}")

# ---------- 阳台开灯 ----------
on = json.load(open("live/1736918907451.json"))
new_on = copy.deepcopy(on)
new_on["description"] = ("阳台暗光(照度<35Lux或日落后)且S04触发；2026-11-10 草案：要求客厅USB雷达15秒内在2.3米内测到走动"
                         "（坐沙发约3.3米、静止不算），通过则开灯并置「阳台有人」锁存；雷达JSON不可用或>60秒未上报时退回旧条件(客厅双雷达有人/3分钟内)且不锁存；S13不参与")
old_gate = on["conditions"][2]   # 客厅双雷达有人 or 180s
assert "ke_ting_shuang_lei_da_you_ren" in json.dumps(old_gate)
new_on["conditions"] = on["conditions"][:2] + [{
    "condition": "or",
    "alias": "客厅雷达近处走动门控(失效时退回旧条件)",
    "conditions": [
        {"condition": "template", "alias": "雷达有效且15秒内2.3米内走动",
         "value_template": FRESH + "{% set nt = as_datetime(states('" + NEAR + "')) %}"
                           "{{ fresh and nt is not none and (now() - nt).total_seconds() <= 15 }}"},
        {"condition": "and", "alias": "雷达失效→旧条件", "conditions": [
            {"condition": "template", "value_template": FRESH + "{{ not fresh }}"},
            old_gate]},
    ]}]
new_on["actions"] = [
    {"variables": {"radar_ok": FRESH + "{{ fresh }}"}},
    copy.deepcopy(on["actions"][0]),
    {"if": [{"condition": "template", "value_template": "{{ radar_ok }}"}],
     "then": [{"action": "input_boolean.turn_on", "target": {"entity_id": LATCH}}]},
]
json.dump(new_on, open("new/1736918907451.json", "w"), ensure_ascii=False, indent=1)

# ---------- 阳台关灯 ----------
off = json.load(open("live/1736942757466.json"))
LATCH_ON = {"condition": "state", "entity_id": LATCH, "state": "on"}
LIGHT_ON = {"condition": "state", "entity_id": LIGHT, "state": "on"}
TURN_OFF = [{"action": "switch.turn_off", "target": {"entity_id": LIGHT}},
            {"action": "input_boolean.turn_off", "target": {"entity_id": LATCH}}]
new_off = {
 "id": off["id"], "alias": off["alias"],
 "description": ("2026-11-10 草案：锁存「阳台有人」期间不按时间关；锁存后≥10秒客厅雷达在2.3米内测到走动=人回客厅→60秒后关"
                 "（期间S04再动或再走动则重新计时/取消）；锁存时S04连续30分钟无动作兜底关；未锁存(手动开/雷达失效开)S04 5分钟无动作关；"
                 "灯关即清锁存；S13不参与"),
 "initial_state": True, "mode": "restart", "max_exceeded": "silent",
 "triggers": [
  {"trigger": "state", "entity_id": NEAR, "not_to": ["unknown", "unavailable"], "id": "exit_walk"},
  {"trigger": "state", "entity_id": S04, "not_to": ["unknown", "unavailable"], "id": "s04_motion"},
  {"trigger": "template", "value_template": idle(1800, True), "id": "latched_30m"},
  {"trigger": "template", "value_template": idle(300, False), "id": "unlatched_5m"},
  {"trigger": "state", "entity_id": LIGHT, "to": "off", "id": "light_off"},
  {"trigger": "homeassistant", "event": "start", "id": "ha_start"},
 ],
 "conditions": [{"condition": "or", "conditions": [
  {"condition": "and", "alias": "回客厅走动：已锁存、灯亮、锁存≥10秒(排除进门那段尾巴)", "conditions": [
     {"condition": "trigger", "id": "exit_walk"}, LATCH_ON, LIGHT_ON,
     {"condition": "template", "value_template": "{{ (now() - states." + LATCH + ".last_changed).total_seconds() >= 10 }}"}]},
  {"condition": "and", "alias": "S04再动：取消待关", "conditions": [
     {"condition": "trigger", "id": "s04_motion"}, LATCH_ON]},
  {"condition": "trigger", "id": ["latched_30m", "unlatched_5m"]},
  {"condition": "and", "conditions": [{"condition": "trigger", "id": ["light_off", "ha_start"]}, LATCH_ON]},
 ]}],
 "actions": [{"choose": [
  {"conditions": [{"condition": "trigger", "id": "exit_walk"}],
   "sequence": [{"delay": {"seconds": 60}}] + TURN_OFF},
  {"conditions": [{"condition": "trigger", "id": "s04_motion"}],
   "sequence": [{"stop": "S04 有动作，取消待关"}]},
  {"conditions": [{"condition": "trigger", "id": ["latched_30m", "unlatched_5m"]}],
   "sequence": TURN_OFF},
  {"conditions": [{"condition": "trigger", "id": ["light_off", "ha_start"]},
                  {"condition": "state", "entity_id": LIGHT, "state": "on", "enabled": True} ],
   "sequence": []},
 ], "default": [
  {"if": [{"condition": "not", "conditions": [LIGHT_ON]}],
   "then": [{"action": "input_boolean.turn_off", "target": {"entity_id": LATCH}}]}]}],
}
# light_off/ha_start：灯亮(重启后灯仍亮)保留锁存；灯不亮清锁存 → 用 default 分支处理，删掉占位分支
new_off["actions"][0]["choose"].pop()
json.dump(new_off, open("new/1736942757466.json", "w"), ensure_ascii=False, indent=1)

# ---------- 巡检阳台分支 ----------
pt = json.load(open("live/auto_lighting_self_healing_patrol.json"))
new_pt = copy.deepcopy(pt)
idx = [i for i, a in enumerate(pt["actions"]) if LIGHT in json.dumps(a)]
assert len(idx) == 1
new_pt["actions"][idx[0]] = {
 "alias": "阳台：锁存时S04 30分钟无动作才关；未锁存S04 5分钟无动作关(2026-11-10 草案)",
 "if": [LIGHT_ON, {"condition": "template", "value_template":
        REF + "{% set idle = (now() - ref).total_seconds() %}"
        "{{ idle >= 1800 if is_state('" + LATCH + "','on') else idle >= 300 }}"}],
 "then": TURN_OFF}
json.dump(new_pt, open("new/auto_lighting_self_healing_patrol.json", "w"), ensure_ascii=False, indent=1)
print("patrol balcony branch index", idx[0])

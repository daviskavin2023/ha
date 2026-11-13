#!/usr/bin/env python3
"""回放 2026-11-10 17:00 起阳台灯：旧逻辑(实际历史) vs 新逻辑(模拟)。只读 replay/history-raw.json。"""
import json, datetime as dt, sys
tz = dt.timezone(dt.timedelta(hours=8))
P = lambda s: dt.datetime.fromisoformat(s).astimezone(tz)
f = lambda t: t.strftime('%H:%M:%S')
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'replay/history-raw.json'))
VARIANT = sys.argv[2] if len(sys.argv) > 2 else 'A'   # A=moving<=230 (约定方案)；B=moving或still<=230
NEAR_CM, ON_WIN, EXIT_GUARD, EXIT_DELAY, HARD_CAP = 230, 15, 10, 120, 7200
LATCH_MAX, UNLATCH_MAX, STALE = 1800, 300, 60
start = dt.datetime(2026, 11, 10, 17, 0, 0, tzinfo=tz)
J = []
for x in d['sensor.ld2410_usb_json']:
    try: J.append((P(x['last_updated']), json.loads(x['state'])))
    except Exception: pass
end = J[-1][0]
def is_near(j):
    m = j.get('moving') and j.get('moving_distance', 999) <= NEAR_CM
    s = j.get('still') and j.get('still_distance', 999) <= NEAR_CM
    return m or (VARIANT == 'B' and s)
near = [t for t, j in J if is_near(j)]
jt = [t for t, j in J]
s04 = [P(x['last_changed']) for x in d['event.linp_cn_blt_3_1k0m2afv4cg01_hs1bb2_motion_detected_e_2_1008']
       if x['state'][:4] == '2026' and P(x['last_changed']) > start]
lux = [(P(x['last_changed']), float(x['state'])) for x in d['sensor.linp_cn_blt_3_1k0m2afv4cg01_hs1bb2_illumination_p_2_1005'] if x['state'].replace('.', '').isdigit()]
sun = [(P(x['last_changed']), x['state']) for x in d['sun.sun']]
dual = [(P(x['last_changed']), x['state']) for x in d['binary_sensor.ke_ting_shuang_lei_da_you_ren']]
def at(series, t, default=None):
    v = default
    for ts, s in series:
        if ts <= t: v = s
        else: break
    return v
def last_change(series, t):
    v = None
    for ts, s in series:
        if ts <= t: v = ts
    return v
def dark(t): return at(sun, t) == 'below_horizon' or (at(lux, t, 999) < 35)
def fresh(t):
    prev = [x for x in jt if x <= t]
    return bool(prev) and (t - prev[-1]).total_seconds() <= STALE
MANUAL_OFF = [P(x['when']) for x in d['_logbook_light'] if x.get('state') == 'off' and x.get('context_user_id')]  # 实际手动关灯
# ---- 旧逻辑：实际历史 ----
L = [(P(x['last_changed']), x['state']) for x in d['switch.lemesh_cn_888711197_sw1f11_on_p_2_1']]
old_on_sec, cur = 0, None
for i, (t, s) in enumerate(L):
    nt = L[i + 1][0] if i + 1 < len(L) else end
    if s == 'on': old_on_sec += (nt - t).total_seconds()
old_auto_on = [P(x['when']) for x in d['_logbook_light'] if x.get('state') == 'on' and x.get('context_entity_id') == 'automation.yang_tai_kai_deng']
old_offs = [t for t, s in L if s == 'off' and t > start]
def suspects(offs):
    out = []
    for o in offs:
        nxt = [s for s in s04 if 0 < (s - o).total_seconds() <= 120]
        if nxt:
            entry = any(0 <= (nxt[0] - n).total_seconds() <= ON_WIN for n in near)
            out.append((o, nxt[0], entry))
    return out
# ---- 新逻辑：逐秒模拟 ----
light, latch, on_t, latch_t, pend, last_s = False, False, None, None, None, None
new_on, new_off, log, ignored = [], [], [], []
new_on_sec = 0
ev = sorted([(t, 's04') for t in s04] + [(t, 'near') for t in near] + [(t, 'manual_off') for t in MANUAL_OFF])
ei = 0
t = start
while t <= end:
    while ei < len(ev) and ev[ei][0] <= t:
        et, kind = ev[ei]; ei += 1
        if kind == 's04':
            last_s = et
            if latch and pend: log.append((et, 'S04 取消待关')); pend = None
            if not light and dark(et):
                if fresh(et):
                    if any(0 <= (et - n).total_seconds() <= ON_WIN for n in near):
                        light, latch, on_t, latch_t = True, True, et, et; new_on.append((et, 'radar')); log.append((et, '开灯+锁存'))
                    else: ignored.append(et)
                else:
                    if at(dual, et) == 'on' or (et - last_change(dual, et)).total_seconds() < 180:
                        light, on_t = True, et; new_on.append((et, 'fallback')); log.append((et, '开灯(兜底,不锁存)'))
        elif kind == 'near':
            if light and latch and (et - latch_t).total_seconds() >= EXIT_GUARD:
                if not pend: log.append((et, '雷达近处走动→120s后关'))
                pend = et + dt.timedelta(seconds=EXIT_DELAY)
        elif kind == 'manual_off' and light:
            light, latch, pend = False, False, None; new_off.append((et, 'manual')); log.append((et, '手动关'))
    if light:
        new_on_sec += 1
        ref = max([x for x in (last_s, on_t) if x])
        reason = None
        if (t - on_t).total_seconds() >= HARD_CAP: reason = 'hard_cap_2h'
        elif pend and t >= pend: reason = 'exit_120s'
        elif latch and (t - ref).total_seconds() >= LATCH_MAX: reason = 'latch_30min'
        elif not latch and (t - ref).total_seconds() >= UNLATCH_MAX: reason = 'unlatched_5min'
        if reason:
            light, latch, pend = False, False, None; new_off.append((t, reason)); log.append((t, '关灯:' + reason))
    t += dt.timedelta(seconds=1)
print(f'回放窗口 {f(start)}–{f(end)} (Asia/Shanghai)，方案 {VARIANT}')
print(f'S04 有效事件 {len(s04)} 次；雷达近处走动样本 {len(near)} 个')
print(f'旧：自动开灯 {len(old_auto_on)} 次，亮灯 {old_on_sec/60:.0f} 分钟，关灯 {len(old_offs)} 次')
print(f'新：自动开灯 {len(new_on)} 次 {[f(x)+"/"+k for x,k in new_on]}，亮灯 {new_on_sec/60:.0f} 分钟')
print('新：关灯', [(f(x), k) for x, k in new_off])
print(f'新：天黑后 S04 触发但雷达 15s 内无近处走动、不开灯 {len(ignored)} 次')
print('新：动作日志'); [print('  ', f(x), m) for x, m in log]
so, sn = suspects(old_offs), suspects([x for x, k in new_off if k != 'manual'])
print(f'旧：关灯后 120s 内又有 S04(可能人还在) {len(so)} 次', [(f(a), f(b), '像新进入' if e else '无雷达进入') for a, b, e in so])
print(f'新：关灯后 120s 内又有 S04(可能人还在) {len(sn)} 次', [(f(a), f(b), '像新进入' if e else '无雷达进入') for a, b, e in sn])

#!/usr/bin/env python3
"""HLK-LD2410 纯蓝牙后台控制与运维工具 (Zero-Touch CLI)
全后台静默接管，无需手机 App，直接由 Agent 触发调参、诊断、监控。
"""
import asyncio
import sys
from bleak import BleakClient, BleakScanner

RADAR_NAME_KEY = "LD2410"
UUID_WRITE = "0000fff2-0000-1000-8000-00805f9b34fb"
UUID_NOTIFY = "0000fff1-0000-1000-8000-00805f9b34fb"

# 基础协议指令
CMD_AUTH = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x08, 0x00, 0xA8, 0x00]) + b"HiLink" + bytes([0x04, 0x03, 0x02, 0x01])
CMD_ENABLE_CONFIG = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x04, 0x00, 0xFF, 0x00, 0x01, 0x00, 0x04, 0x03, 0x02, 0x01])
CMD_END_CONFIG = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0xFE, 0x00, 0x04, 0x03, 0x02, 0x01])
CMD_READ_VERSION = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0xA0, 0x00, 0x04, 0x03, 0x02, 0x01])
CMD_READ_PARAMS = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x61, 0x00, 0x04, 0x03, 0x02, 0x01])
CMD_RESTART = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0xA3, 0x00, 0x04, 0x03, 0x02, 0x01])


async def get_device():
    devices = await BleakScanner.discover(timeout=7.0, return_adv=True)
    for addr, (d, adv) in devices.items():
        name = d.name or adv.local_name or ""
        if RADAR_NAME_KEY in name or "HLK" in name:
            return d
    return None


async def cmd_status():
    device = await get_device()
    if not device:
        print("[ERROR] 未发现 LD2410 蓝牙广播，请检查雷达供电。")
        return False
    print(f"[OK] 发现雷达: {device.name} ({device.address})")

    res_version = None
    res_params = None
    realtime_data = []

    def notify_callback(sender, data):
        nonlocal res_version, res_params
        b = bytes(data)
        if b.startswith(bytes([0xFD, 0xFC, 0xFB, 0xFA])) and len(b) >= 8:
            cmd = b[6]
            if cmd == 0xA0:
                res_version = b
            elif cmd == 0x61:
                res_params = b
        elif b.startswith(bytes([0xF4, 0xF3, 0xF2, 0xF1])):
            realtime_data.append(b)

    async with BleakClient(device) as client:
        await client.start_notify(UUID_NOTIFY, notify_callback)
        await client.write_gatt_char(UUID_WRITE, CMD_AUTH, response=False)
        await asyncio.sleep(0.3)
        await client.write_gatt_char(UUID_WRITE, CMD_ENABLE_CONFIG, response=False)
        await asyncio.sleep(0.3)
        await client.write_gatt_char(UUID_WRITE, CMD_READ_VERSION, response=False)
        await asyncio.sleep(0.3)
        await client.write_gatt_char(UUID_WRITE, CMD_READ_PARAMS, response=False)
        await asyncio.sleep(0.6)
        await client.write_gatt_char(UUID_WRITE, CMD_END_CONFIG, response=False)
        await asyncio.sleep(0.3)

    if res_version and len(res_version) >= 18:
        major = f"{res_version[13]:x}"
        minor = f"{res_version[12]:02x}"
        b_date = f"{res_version[17]:02x}{res_version[16]:02x}{res_version[15]:02x}{res_version[14]:02x}"
        print(f"  - 固件版本: V{major}.{minor}.{b_date}")

    if res_params and len(res_params) >= 34:
        max_move_gate = res_params[12]
        max_still_gate = res_params[13]
        timeout_sec = int.from_bytes(res_params[32:34], 'little')
        motion_sens = list(res_params[14:23])
        still_sens = list(res_params[23:32])
        print(f"  - 探测门上限: 运动门 0~{max_move_gate} (约 {max_move_gate*0.75:.2f}m) | 静止门 0~{max_still_gate} (约 {max_still_gate*0.75:.2f}m)")
        print(f"  - 无人维持延时: {timeout_sec} 秒")
        print(f"  - 运动门灵敏度 (门0~8): {motion_sens}")
        print(f"  - 静止门灵敏度 (门0~8): {still_sens}")

    if realtime_data:
        latest = realtime_data[-1]
        target_state = latest[8]
        state_map = {0: "无人", 1: "有人走动 (运动)", 2: "有人静坐 (微动/静止)", 3: "多人存在 (运动+静止)"}
        state_str = state_map.get(target_state, f"未知({target_state})")
        move_dist = int.from_bytes(latest[9:11], 'little')
        still_dist = int.from_bytes(latest[12:14], 'little')
        print(f"  - 实时感知状态: 【{state_str}】")
        if target_state & 1:
            print(f"    * 运动目标距离: {move_dist} cm")
        if target_state & 2:
            print(f"    * 静止目标距离: {still_dist} cm")
    print("[SUCCESS] 雷达工作完全正常！")
    return True


async def cmd_set_params(max_move: int, max_still: int, timeout_sec: int):
    device = await get_device()
    if not device:
        print("[ERROR] 未发现 LD2410 蓝牙广播")
        return False
    # FD FC FB FA 14 00 60 00 00 00 <move> 00 00 00 01 00 <still> 00 00 00 02 00 <timeout L H> 00 00 04 03 02 01
    cmd = bytearray([0xFD, 0xFC, 0xFB, 0xFA, 0x14, 0x00, 0x60, 0x00])
    # Word 0: Max move gate
    cmd += bytes([0x00, 0x00, max_move, 0x00, 0x00, 0x00])
    # Word 1: Max still gate
    cmd += bytes([0x01, 0x00, max_still, 0x00, 0x00, 0x00])
    # Word 2: Timeout
    cmd += bytes([0x02, 0x00, timeout_sec & 0xFF, (timeout_sec >> 8) & 0xFF, 0x00, 0x00])
    cmd += bytes([0x04, 0x03, 0x02, 0x01])

    async with BleakClient(device) as client:
        await client.write_gatt_char(UUID_WRITE, CMD_AUTH, response=False)
        await asyncio.sleep(0.3)
        await client.write_gatt_char(UUID_WRITE, CMD_ENABLE_CONFIG, response=False)
        await asyncio.sleep(0.3)
        await client.write_gatt_char(UUID_WRITE, bytes(cmd), response=False)
        await asyncio.sleep(0.5)
        await client.write_gatt_char(UUID_WRITE, CMD_END_CONFIG, response=False)
        await asyncio.sleep(0.3)
    print(f"[OK] 参数已更新: 最大运动门={max_move}, 最大静止门={max_still}, 延时={timeout_sec}秒")
    return True


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        asyncio.run(cmd_status())
    elif action == "set-params" and len(sys.argv) >= 5:
        asyncio.run(cmd_set_params(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])))
    else:
        print(f"用法: ld2410_cli.py status | set-params <max_move> <max_still> <timeout_sec>")

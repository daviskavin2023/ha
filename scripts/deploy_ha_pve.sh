#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# 3038-网关-ha: PVE 10 (10.10.10.10) 自动化部署 HAOS 虚拟机 (VMID 138)
# ==============================================================================

VMID=138
VM_NAME="haos-138"
CORES=2
RAM=4096
DISK_SIZE="32G"
STORAGE="local-lvm"
BRIDGE="vmbr0"
MAC="BC:24:11:10:10:38"
HAOS_VERSION="18.2"
IMG_URL="https://github.com/home-assistant/operating-system/releases/download/${HAOS_VERSION}/haos_ova-${HAOS_VERSION}.qcow2.xz"
TMP_DIR="/tmp"
XZ_FILE="${TMP_DIR}/haos_ova-${HAOS_VERSION}.qcow2.xz"
QCOW_FILE="${TMP_DIR}/haos_ova-${HAOS_VERSION}.qcow2"

echo "=== [1/7] 检查与准备环境 ==="
if qm status "${VMID}" &>/dev/null; then
  echo "警告: VMID ${VMID} 已存在！正在停止并销毁旧实例..."
  qm stop "${VMID}" || true
  sleep 2
  qm destroy "${VMID}" --purge || true
fi

echo "=== [2/7] 下载 HAOS 官方镜像 (${HAOS_VERSION}) ==="
if [ ! -f "${QCOW_FILE}" ]; then
  if [ ! -f "${XZ_FILE}" ]; then
    echo "从 GitHub 下载: ${IMG_URL} ..."
    wget -q --show-progress -O "${XZ_FILE}" "${IMG_URL}"
  else
    echo "找到已存在的压缩镜像: ${XZ_FILE}"
  fi
  echo "解压镜像..."
  xz -d -f -k "${XZ_FILE}"
fi

echo "=== [3/7] 创建基础虚拟机 (Q35 + UEFI + 4G RAM + 2 vCPU) ==="
qm create "${VMID}" \
  --name "${VM_NAME}" \
  --machine q35 \
  --bios ovmf \
  --ostype l26 \
  --cores "${CORES}" \
  --cpu host \
  --memory "${RAM}" \
  --balloon 0 \
  --net0 "virtio=${MAC},bridge=${BRIDGE},firewall=0" \
  --onboot 1 \
  --agent 1 \
  --description "Home Assistant OS 3038 (IP: 10.10.10.38/24, GW/DNS: 10.10.10.15)"

echo "=== [4/7] 创建 EFI 磁盘与导入存储盘 ==="
qm set "${VMID}" --efidisk0 "${STORAGE}:0,efitype=4m,pre-enrolled-keys=0"
echo "导入磁盘镜像到 ${STORAGE} ..."
qm importdisk "${VMID}" "${QCOW_FILE}" "${STORAGE}"

echo "=== [5/7] 挂载磁盘并调整大小至 ${DISK_SIZE} ==="
# 查找导入的未分配磁盘
UNUSED_DISK=$(qm config "${VMID}" | grep -o "unused[0-9]*: [^ ]*" | head -n 1 | awk '{print $2}')
if [ -z "${UNUSED_DISK}" ]; then
  # 兜底命名规则
  UNUSED_DISK="${STORAGE}:vm-${VMID}-disk-1"
fi
echo "挂载磁盘: ${UNUSED_DISK} 到 scsi0 ..."
qm set "${VMID}" --scsihw virtio-scsi-single --scsi0 "${UNUSED_DISK},discard=on,ssd=1,iothread=1"
qm set "${VMID}" --boot order=scsi0

echo "扩容 scsi0 至 ${DISK_SIZE} ..."
qm resize "${VMID}" scsi0 "${DISK_SIZE}"

echo "=== [6/7] 清理临时镜像文件 ==="
rm -f "${XZ_FILE}" "${QCOW_FILE}"

echo "=== [7/7] 启动 HAOS 虚拟机 (VM 138) ==="
qm start "${VMID}"

echo "=========================================================================="
echo "✅ HAOS (VM 138) 创建并启动成功！"
echo "MAC 地址: ${MAC}"
echo "分配 IP: 10.10.10.38 (待 DHCP 绑定或控制台锁定)"
echo "网关/DNS: 10.10.10.15"
echo "=========================================================================="

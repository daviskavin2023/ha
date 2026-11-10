#!/bin/zsh
# 阳台灯 2026-11-10 回滚（在 Mac 上、项目根目录执行）。不打印 token。
set -e
cd ~/Projects/yulaiwo/3038-网关-ha
B=backups/balcony-light-20261110-233027
python3 -c "import json;print(json.dumps({k:json.load(open('$B/'+k+'.json')) for k in ['1736918907451','1736942757466','auto_lighting_self_healing_patrol']},ensure_ascii=False))" | \
ssh -o BatchMode=yes -o ProxyJump=gw15 ct115 'python3 -c "
import json,sys,urllib.request
T=open(\"/data/ylwzs/ha-token\").read().strip()
H={\"Authorization\":\"Bearer \"+T,\"Content-Type\":\"application/json\"}
def post(p,d): urllib.request.urlopen(urllib.request.Request(\"http://10.10.10.38:8123\"+p,data=json.dumps(d).encode(),headers=H,method=\"POST\"),timeout=60)
for k,v in json.load(sys.stdin).items(): post(\"/api/config/automation/config/\"+k,v); print(\"restored\",k)
post(\"/api/services/automation/reload\",{}); print(\"automation reloaded\")"'
C=/mnt/data/supervisor/homeassistant/configuration.yaml
ssh -o BatchMode=yes -o ProxyJump=gw15 -p 22222 root@10.10.10.38 "cp $C.bak.20261110-233027-balcony $C && ha core check"
ssh -o BatchMode=yes -o ProxyJump=gw15 ct115 'python3 -c "
import json,urllib.request
T=open(\"/data/ylwzs/ha-token\").read().strip()
H={\"Authorization\":\"Bearer \"+T,\"Content-Type\":\"application/json\"}
for s in [\"input_boolean/reload\",\"template/reload\"]:
    urllib.request.urlopen(urllib.request.Request(\"http://10.10.10.38:8123/api/services/\"+s,data=b\"{}\",headers=H,method=\"POST\"),timeout=60); print(\"reloaded\",s)"'
cp $B/{1736918907451,1736942757466,auto_lighting_self_healing_patrol}.json exports/automations/

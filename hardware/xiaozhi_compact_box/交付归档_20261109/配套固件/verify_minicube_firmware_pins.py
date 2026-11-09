from pathlib import Path
import json,re
ROOT=Path('/Users/kavin/.codex/visualizations/2026/11/08/xiaozhi-hardware-review')
OUT=Path('/Users/kavin/Desktop/小智小方盒_修复交付_20261109')
B=ROOT/'firmware-upstream-v2.5.2/main/boards/xiaozhi-minicube'
header=(B/'config.h').read_text()
pins={n:int(v) for n,v in re.findall(r'^#define (\w+) GPIO_NUM_(\d+)$',header,re.M)}
carrier={(p['ref'],p['pin']):p for p in json.loads((OUT/'底板引脚数据.json').read_text())}
links=[('MIC_DATA_PIN','J_MIC','3'),('MIC_WS_PIN','J_MIC','5'),('MIC_SCK_PIN','J_MIC','6'),
 ('DAC_BCK_PIN','J_DAC_IN','3'),('DAC_LRCK_PIN','J_DAC_IN','5'),('DAC_DATA_PIN','J_DAC_IN','4'),
 ('AMP_SD_PIN','J_AMP_IN','3'),('RADAR_OUT_PIN','J_RADAR','3'),
 ('TOUCH_SDA_PIN','J_LCD_PWR','4'),('TOUCH_SCL_PIN','J_LCD_PWR','3'),
 ('DISPLAY_MOSI_PIN','J_LCD_SPI','1'),('DISPLAY_DC_PIN','J_LCD_SPI','2'),
 ('DISPLAY_CLK_PIN','J_LCD_SPI','3'),('DISPLAY_CS_PIN','J_LCD_SPI','4')]
report=[]
for symbol,ref,pin in links:
 p=carrier[ref,pin]
 n=int(re.search(r'IO(\d+)$',p['name'])[1])
 assert pins[symbol]==n,(symbol,pins[symbol],p)
 assert n not in {0,3,35,36,37,43,44,45,46},(symbol,n)
 report.append(dict(symbol=symbol,gpio=n,carrier=f'{ref}.{pin}',net=p['name']))
assert len({x['gpio'] for x in report})==len(report)
cc=(B/'minicube_board.cc').read_text()
assert cc.count('DECLARE_BOARD(')==1
assert 'LampController' not in cc
assert 'GPIO_NUM_18' not in cc
assert '#define DISPLAY_RST_PIN GPIO_NUM_NC' in header
assert '#define DISPLAY_BACKLIGHT_PIN GPIO_NUM_NC' in header
assert 'SPARE_RX'==carrier['J_ESP_R1','3']['name']
assert 'SPARE_TX'==carrier['J_ESP_R1','2']['name']
print(json.dumps(dict(result='PASS',functional_mappings=report,duplicate_GPIO=0,
 unidentified_BL_RST_INT_driven=False,service_UART_pins_match=True,
 native_firmware_compile_checked_by_this_script=False,hardware_run_checked_by_this_script=False),ensure_ascii=False,indent=2))

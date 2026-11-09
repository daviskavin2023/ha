"""Compile the actual board's amp-gate class against deterministic IDF stubs."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path('/Users/kavin/.codex/visualizations/2026/11/08/xiaozhi-hardware-review')
text=(ROOT/'firmware-upstream-v2.5.2/main/boards/xiaozhi-minicube/minicube_board.cc').read_text()
actual='class MinicubeCodec'+text.split('class MinicubeCodec',1)[1].split('class MinicubeBoard',1)[0]
stub=r'''
#include <mutex>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#define AUDIO_INPUT_SAMPLE_RATE 16000
#define AUDIO_OUTPUT_SAMPLE_RATE 24000
#define DAC_BCK_PIN 7
#define DAC_LRCK_PIN 15
#define DAC_DATA_PIN 16
#define MIC_SCK_PIN 6
#define MIC_WS_PIN 5
#define MIC_DATA_PIN 4
#define AMP_SD_PIN 9
#define ESP_ERROR_CHECK(x) assert((x)==0)
std::atomic<int> sd{0};
int64_t now_us=0;
int gpio_set_level(int pin,int level) {assert(pin==9);sd=level;return 0;}
int64_t esp_timer_get_time() {return now_us;}
struct esp_timer_create_args_t {void (*callback)(void*)=nullptr;void* arg=nullptr;const char* name=nullptr;};
struct Timer {esp_timer_create_args_t cfg;bool active=false;};
using esp_timer_handle_t=Timer*;
Timer timer;
int esp_timer_create(esp_timer_create_args_t* cfg, esp_timer_handle_t* out) {timer.cfg=*cfg;*out=&timer;return 0;}
int esp_timer_stop(Timer* t) {t->active=false;return 0;}
int esp_timer_start_once(Timer* t,int64_t delay) {assert(delay==10000);t->active=true;return 0;}
class NoAudioCodec {protected:bool output_enabled_=false;virtual void EnableOutput(bool b){output_enabled_=b;}};
class NoAudioCodecSimplex:public NoAudioCodec {public:NoAudioCodecSimplex(int,int,int,int,int,int,int,int) {}};
'''
tests=r'''
int main() {
 MinicubeCodec c;
 c.EnableOutput(true); assert(sd==0);
 now_us=9999; timer.cfg.callback(timer.cfg.arg); assert(sd==0);
 now_us=10000; timer.cfg.callback(timer.cfg.arg); assert(sd==1);
 c.EnableOutput(true); assert(sd==1); // redundant enable must not re-mute
 c.EnableOutput(false); assert(sd==0);
 now_us=20000; timer.cfg.callback(timer.cfg.arg); assert(sd==0);
 c.EnableOutput(true); assert(sd==0);
 now_us=21000; timer.cfg.callback(timer.cfg.arg); assert(sd==0); // stale callback
 now_us=30000; timer.cfg.callback(timer.cfg.arg); assert(sd==1);
 c.EnableOutput(false); assert(sd==0);
 puts("PASS: startup mute, 10ms gate, redundant enable, disable, stale timer callback");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.cc';p.write_text(stub+actual+tests)
 exe=Path(d)/'amp-test'
 subprocess.run(['/usr/bin/clang++','-std=c++17','-Wall','-Wextra','-Werror',str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

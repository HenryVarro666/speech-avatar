# E5a 真实TTS流：运行、验证与恢复

当前[本地预览](http://127.0.0.1:50451/index.html)每次实际生成新声音，支持Serena／Uncle_Fu与4条新中文开发文本。它是独立CPU试用，不修改原DSH服务或旧57383页。结果：[7请求与性能](../experiments/2026-10-24-e5-live-tts/RESULTS.md)。

## 如何操作

1. 选择语句、人物，点击“生成并播放”。本轮CPU首PCM约3.1–5.4s，显示“等下一块／欠载”时确实在等待下一块，不能当作网络无故卡死。
2. 播放中点击“插话：更正预约”：停旧声、取消旧生成、以新ID合成更正句。“立即打断”只停止当前轮次。此按钮事件不是麦克风识别结果。
3. “真实流传两块后断开”会实际截断本轮传输，界面应显示音频不完整；点击“重试本句（从头）”明确重合成整句，或者换新句。不会自动重播已说前缀。
4. “注入上一轮迟到错误”应只增加丢弃记录，不改变新轮次状态。“导出实验记录”保存在本机，人工音画接受仍null。

已有音色的接受不等于新句的内容/自然度接受。源PCM24kHz/单声道/s16le保持原采样率进入同一ReplySpeaker；浏览器可能按硬件输出率重采样，未测扬声器物理首声或波形一致性。

## 服务组成与重新准备

`workers/realtime_tts/worker.py`是独立CPU模型服务，绑定远端127.0.0.1的独立端口；`scripts/e5_service.py`在Mac同源代理并提供页面，SSH只转发这一个新端口。使用现存qwen-tts0.1.1/torch2.8.0环境及固定模型；不启动原bridge，不安装共享包。固定ABI/hash与流格式见[SETUP](../workers/realtime_tts/SETUP.md)。

需要原私有头像/贴片及模型缓存。公开仓库不包含这些文件。准备本机视觉资源（不复制录音）：

```bash
cd /path/to/projects/speech-avatar
python3.12 scripts/prepare_e5_preview.py
# 已存在且确需更新本轮页面时，显式加 --refresh
```

模型worker须在一个新的尝试目录启动，其中先复制manifest.json、runtime-pin.json和本轮workers源码；既有worker.json会阻止覆盖。当前CPUaffinity80–83按此96核机器选定，其他机器需要调整为实际允许的空闲核并重新记录。启动示例：

```bash
python -m workers.realtime_tts.worker --root NEW_ATTEMPT --prior EXISTING_E1B_TTS
```

`--prior`包含原.venv与model/model_manifest.json，所有读取文件按固定hash核验。端口写入新目录worker.json；SSH用`-L 127.0.0.1:LOCAL_PORT:127.0.0.1:WORKER_PORT`转发。然后在Mac启动代理：

```bash
python3.12 scripts/e5_service.py --root outputs/e5 \
  --upstream http://127.0.0.1:LOCAL_PORT \
  --ledger PRIVATE_EVENTS_JSONL --receipt PRIVATE_SERVER_JSON
```

实际本轮端口/PID存于本地实验forward.json、preview-server.json及RAID worker.json；使用前核对本轮身份，不操作其他预览或原服务。页面缺模型连接时显示不可用；恢复SSH/自有worker后重新打开页面发新请求。停止试用时只按这些回执核验并关闭本轮进程；模型驻留和原共享模型是不同进程。

## 故障语义

取消先在客户端立即失效epoch并停声，再Abort fetch和发对应requestId的cancel；上游以合作式检查退出当前模型调用。新请求等待其模型锁释放。提前cancel有墓碑，晚到的同ID请求不会开始生成。重复cancel幂等；其时间字段记录最近请求，不作为首个取消耗时。

传输消息必须从start开始，audio的seq/offset连续，最后有匹配samples的end。HTTP EOF、模型异常或缺end都属于不完整。结束摘要SHA与保存源PCM核对，客户端采样数另核对；物理播放结束由播放器状态另记。失败/取消后的显式新请求使用新ID，不复用旧任务或旧视频。

目前CPU RTF3.13–3.59且最大计划音频空隙2.84s，**尚不适合低延迟实战**。下一阶段先取得空闲GPU并测同协议的持续速度/首块，再接麦克风/VAD/ASR/翻译和长回复切句；真人回声/插话与中文听感必须独立验收。

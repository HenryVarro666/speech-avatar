# E5a 实际TTS流与隔离播放器

2026-10-24 America/Chicago。用户明确要求继续既定E5，在隔离实例接真实TTS流、验证换句/插话打断/断流恢复、打开预览、记录并推送。本计划延续已批准的单播放器/epoch/视觉降级方案，直接实施；不另设重复审批。用户禁止未授权子代理，故本人实现/复核；原目录开发，公开备份审查后按本次明确授权push，不从原DSH历史推送。

## 固定设计与边界

复用原固定Qwen3-TTS1.7BCustomVoice模型/Serena与Uncle_Fu；4条新开发文本在manifest冻结，非held-out集，无真人/新句音画接受。两GPU均忙，独立H100新RAID目录，CPU-only、nice19、4线程、80–83核（与并行异步试验88–91不同）；只读原环境/权重，不安装/修改vendor，不访问apex/重启共享服务。运行前/后核验原服务启动、资源与自有进程；内存/请求/生成长度/时间均有界。

官方generate_custom_voice在整句后返回；本轮固定版本适配器从talker真实forward输出捕获16码本帧，每12帧用官方12Hzdecoder及25帧左上下文解码，逐块发送新PCM。核对捕获codes与本次官方generate返回codes完全一致；保存首块和生成结束时间，禁止整句后切片冒充流式。生成/codec/传输音质与速度是新待验条件，不能自动继承旧配音接受。CPU慢导致的真实欠载必须记录。

服务只监听远端loopback，经独立SSH转发到Mac隔离HTTP代理；新浏览器页同源请求，密钥/环境/模型路径不进浏览器。PCM NDJSON消息有requestId、rate24000、单声道PCM16、seq、offset、bytes、结束samples/hash；浏览器转为既有ReplySpeaker输入。明确end缺失就是incomplete，不能把HTTP EOF当成功。一个播放器发声，音频时钟驱动既有HeadAudio/WebGL贴片；视觉准备并行，不改旧E2–E4页。

取消会立即停本机音源、提升epoch、AbortController断fetch，代理再取消对应上游任务。模型hook检查取消并停止自身生成，串行模型锁释放后下一句进入；旧完成/错误不得覆盖新句。断流注入作用于真实生成后的传输，明确保留部分语音；恢复由显式新请求/从头重试完成，不自动重播已说前缀。控制按钮触发插话事件验证取消链，真人麦克风/回声/ASR/翻译另列pending。

## 文件与验收步骤

- [x] `workers/realtime_tts/streaming.py`真实码帧分块/取消适配，`worker.py`只读加载固定模型、受限HTTP和私有原始回执；先以真实CPU短句证明首块早于生成完成，codes/样本/hash完整。
- [x] `scripts/e5_service.py`仅loopback代理/静态页/按ID取消，真实断流和已收块统计。子进程/队列/错误消息边界单元测试先RED后GREEN；只终止自有worker。
- [x] `web/e5/transport.mjs`验证消息ID/seq/offset/end，缺end/格式错误拒绝，旧轮次隔离；Node契约先RED后GREEN。新`app.mjs/index.html`接真实fetch流和同一ReplySpeaker，独立输出目录复制旧视觉资源但不覆盖旧证据。
- [x] 浏览器实际完成女/男不同句子；在有声块中触发更正并验证旧请求取消/新句恢复；传输截断→incomplete→显式新句恢复；记录实际首块、调度首声起点、最大欠载、服务取消、尾部完整和视图降级。人声学/自然度不由技术验收代签。
- [x] 更新双语README、技术路线、两边状态/历史、总账及公开摘要；新增8份元数据逐文件allowlist，完成首轮preview/showdiff与扫描审查。最后发布动作按下方独立检查点执行，不把候选当已推送；模型、vendor、凭据、原始音视频不发布。

## 自审重点

模型内部hook需版本/hash硬检查；prefill无code、EOS、非完整尾块、取消发生于prefill/解码、流EOF无end、角色切换、新旧请求并发和代理客户端断开都有验证。服务端生成完成、浏览器收完和实际播放结束分别记录；0PCM错误不得算complete。仅E5真实TTS子阶段，不称完整实时口译部署。并行E2异步试验文件不锁入本轮父文件不回滚；其未审核进度不顺带推送。

## Publication checkpoint

本计划的技术/文档准备已完成；用户本轮授权的实际push须使用最终重新生成、hash/链接检查通过的候选。远端提交/树与原sourceGit不变的核验保存在独立PUBLICATION_RECEIPT.json和工具push-receipts中，最终状态入口另记，发布前不伪造提交号。

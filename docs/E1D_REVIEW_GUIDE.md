# E1d 回放与人工反馈

2026-10-23。E1d男女两段新片已经完成，不需要重新渲染。质量结论仍是 NEEDS WORK；本轮续接补的是反馈保存与恢复检查，不是新的模型实验。

## 当前怎样操作

1. 打开 [本机预览](http://127.0.0.1:54954/index.html)，按角色看A/B。先观察口型、牙齿、表情、手部、头顶构图和3.72秒续接，再决定是否揭示处理方式。
2. 在页底分别填“构图偏好”和“音画接受”。更喜欢A或B不会自动判定音画可接受；无明显差别、两段都不可接受、只看了一个角色都可以如实记录。问题栏可写时间点。
3. 点“导出我的反馈”，得到 `e1d-feedback-draft.json`。反馈仅保留在当前页面，刷新或关闭前先导出；这不是自动提交，也不会修改实验中的 `user_review.json`。
4. 将真实反馈文件交回后，先核对冻结manifest、四段视频SHA与A/B映射，再归档实际人工意见。缺失判断保持null，不能凭模型分数或偏好推断验收通过。导出还记录处理名是否已揭示，不能把已揭示评价称为严格盲评。

导出始终标记 `review_status=draft`。本轮浏览器验收用了明确标为QA的合成填写，保存在被忽略的 `outputs/e1d/recovery-20261023-v1/qa-*.json`；它们不是人的评价，不得导入为用户验收。

## 中断后怎样恢复

当前本机服务仍在54954端口。CPU测试需要Python3.12、Node.js18+及ffmpeg/ffprobe。只更新预览和反馈代码时运行：

```bash
python3.12 scripts/prepare_e1d_preview.py
python3.12 -m unittest discover -s tests -v
```

然后刷新已有标签。该命令校验/复制现有媒体并保留已有 `user_review.json`，不调用GPU。服务已经停止时，可以在新空闲端口重开：

```bash
python3.12 -m http.server 0 --bind 127.0.0.1 --directory outputs/e1d
```

打开输出端口对应的 `index.html`。不要停止其他本机服务器来腾端口。原始渲染、数值、协议和旧验收快照保持不变，本轮新取证单独放在实验的 `recovery-20261023-v1/`。

## 远端状态与下一轮

另一项已完成的迁移将H100 Avatar规范路径改为 `/mnt/raid/voice_ai/speech-avatar`，旧 `/data/speech-avatar-exx-20261020` 保留兼容链接。未来需要远端任务时先使用：

```bash
source /mnt/raid/voice_ai/env.sh
cd /mnt/raid/voice_ai/speech-avatar
```

历史manifest和执行命令不重写。此次只读确认路径可达，两张GPU均有其他任务；没有启动渲染或操作这些进程。后续新推理仍需独立资源预检。

另一个任务已经完成DUIX单段技术出片，但质量、同步和有声尾帧仍需工作；它不构成E1d人工接受，也不表示已经接入实时对话。本轮不扩展该实验。后续先收集现有片真实反馈，再选择显式动作条件/rig或另行冻结的同步尾帧小实验，避免继续同一裁切/seed网格。

# Speech Avatar

[English](README.md) · **简体中文**

**验证音频驱动头像能否成为清晰、有表情的语音 Agent 视觉界面。**

## 问题与目标场景

语音 Agent 配上头像，不能只让嘴动：身份要稳定，音画要对齐，表情要自然，手、牙齿和片尾不能干扰语音信息。

本项目开发未来说话助手或口译型界面的生成与审阅层。ASR、对话、翻译和预约状态属于其他项目。离线生成可用不代表口译产品已部署，也不代表实时数字人。

## 使用与探索的方法

固定合成语音和两个虚构静态头像，离线比较 MuseTalk1.5 / LongCat1.5。审阅结合完整解码/源音轨检查、动态嘴部/全景检查、SyncNet 偏移诊断与平衡顺序的本地人工对照。

MuseTalk 保留为低成本口型/回归基线；LongCat 是离线完整表情开发候选。两者均未通过精修视频或实时对话验收，OmniAvatar、Hunyuan 尚未运行。

## 当前结果与决定

| 阶段 | 做了什么 | 结论与决定 |
|---|---|---|
| [E0 输入](experiments/2026-10-20-e0/RESULTS.md) | 12 开发＋24 测试合成语音，两个虚构头像 | 结构冻结；媒体留本地 |
| [E1 MuseTalk](experiments/2026-10-20-e1-musetalk/RESULTS.md) | 12 个离线组合；首保存帧/完整任务中位 3.003/7.165 秒，RTF1.999 | 解码/音轨通过；齿列糊、头眼静止及收尾待改善 |
| [E1b 后端对照](experiments/2026-10-20-e1b-full-expression/RESULTS.md) | 同一已接受男女配音分别驱动两个后端，共四片 | MuseTalk 整进程 23.916/23.607 秒；LongCat 270.721/267.728 秒；表情增加但强度、齿列和手入画仍有问题 |
| [E1b 质量审查](experiments/2026-10-20-e1b-full-expression/quality-review-v1/REVIEW.md) | 516 嘴帧、108 全景及同步细节；模型偏移控制 | LongCat 继续离线开发、MuseTalk 留基线；NEEDS WORK |
| [E1c 受控优化](experiments/2026-10-21-e1c-controlled-expression/RESULTS.md) | 六份 0/40/80ms 同步副本＋两段受控提示 LongCat 新片 | 只改提示未解决手入画/强调张嘴；按门槛跳过收尾生成（0 段） |

E1 计时不含共享模型加载；E1b/E1c 整进程包含加载，不能当同口径比较或语音对话视频延迟。E1c 两新片整进程 267.418/263.161 秒，640×608/25fps。

原 E1b LongCat 的 SyncNet 估计女/男画面领先 80/40ms。延后副本用于人工比较，不自动作为同步验收。人工连续音画评分待做，≥10/12 质量门槛尚未通过。

## 实验如何记录

[阶段索引](experiments/INDEX.md)链接冻结计划、清单、结果与审查决定。失败尝试全部保留。公开提示、哈希、汇总诊断和脚本；录音、头像、渲染视频、检查拼图及模型/vendor 目录留本地。

## 验证与复现

Python3.12 CPU 契约不运行生成模型：

```bash
python3.12 -m unittest discover -s tests -v
```

本地保有对应私有输入时，再运行：

```bash
python3.12 scripts/validate_e0.py experiments/2026-10-20-e0/manifest.json
```

GPU 推理需要独立的 [MuseTalk](workers/musetalk/SETUP.md) / [LongCat](workers/longcat/SETUP.md) 环境、模型权限和冻结计划，不声称实时数字人一键安装已验证。

## 下一步

1. 收集现有同步及原片/新片对照的人工判断。
2. 单独冻结一种更强构图/动作条件假设；只改提示未建立收益。
3. 先看到质量改善，再进入有条件中性收尾实验。
4. 浏览器实时生成及语音 Agent 接入作为后续独立阶段。

[技术边界](docs/TECHNICAL_ROUTE.md) · [当前状态](PROJECT_STATUS.md) · [公开范围](PUBLICATION.md) · [工作区](https://github.com/HenryVarro666/voice-ai-workspace)。

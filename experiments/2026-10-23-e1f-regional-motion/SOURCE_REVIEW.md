# 显式控制路径核对与选择

2026-10-23，实际固定源码与官方链接并核对。LivePortrait commit `9b294b3d0536135442ea73cb01e6cb3ca7029dd3`，human weights `82a4fa6735ca58432b6ce39301b4b9ee066dea47`。

| 路径 | 已核对接口及限制 | 决定 |
|---|---|---|
| LongCat原生单人CLI | ai2v参考图和avc续接；未建立单独骨骼/驱动视频控制。E1d已核对条件视频是续接语义 | 不重复裁切/提示网格，也不把续接接口当动作驱动 |
| LivePortrait全局幅度 | E1e可驱动头眼，但0.65同时削弱闭眼/嘴动；仅女性验证 | 不再只整体压低 |
| LivePortrait WIP眼/唇重定向 | 相对运动分支直接设target=source+retarget deltas，会覆盖既有pose displacement | 不直接开关；避免退回静止头部 |
| **分区原生驱动模板** | make_motion_template暴露R/exp/t/scale；眼区索引11/13/15/16/18；原生relative/all消费这些参数再stitching | **选定**。先在复制模板上做相对首帧分区增益，原生global1.0，保留头姿路径 |

精确形式：R'i=Exp(0.65 Log(Ri R0ᵀ))R0；t'i=t0+0.65(ti−t0)；s'i=s0+0.65(si−s0)；exp'i=exp0+g⊙(expi−exp0)，eye indices g=1.0，其余0.65。x_s诊断随上述参数重算，kp不改。原生expression-friendly补偿/stitching仍会改变最终幅度，因此参数增益不等于图像中测得比例，必须保留执行轨迹和输出诊断。

该方案是本实验自定义模板适配，不称官方一键眼睑独立控制。两角色复用同一规则，生成前冻结。即使没有手入画，也只是静态原图背景保留，非全身人物手部生成能力。牙齿纹理仍由256面部网络产生，无预设修复承诺。

来源：[官方pipeline](https://github.com/KlingAIResearch/LivePortrait/blob/9b294b3d0536135442ea73cb01e6cb3ca7029dd3/src/live_portrait_pipeline.py)、[wrapper](https://github.com/KlingAIResearch/LivePortrait/blob/9b294b3d0536135442ea73cb01e6cb3ca7029dd3/src/live_portrait_wrapper.py)、[参数](https://github.com/KlingAIResearch/LivePortrait/blob/9b294b3d0536135442ea73cb01e6cb3ca7029dd3/src/config/argument_config.py)、[此前LongCat核对](../2026-10-23-e1d-reference-framing/SOURCE_REVIEW.md)。官方源码只供取证，不纳入公开源码包。

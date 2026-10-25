# LongCat 控制路径核对与本轮选择

2026-10-23。对照当前官方页面与实际 H100 固定源码；实际 pipeline 与官方固定 commit 逐字节相同，记录在 [source_audit.json](source_audit.json)。固定版本仍为 `6b3f4b8582a8bc3f20f795735f5383716c4ba794`，没有升级模型或环境。

| 路径 | 实际作用 | 本轮决定 |
| --- | --- | --- |
| 正面／负面提示、steps／CFG | 原生 v1.5 蒸馏入口覆盖 steps 为8、text/audio CFG为1；该配置不进入负面提示编码分支 | E1c 已观察到提示控制不足，不追加文字或无效网格。当前官方文档要求v1.5启用蒸馏，不能把非蒸馏当已支持方案。 |
| ai2v 参考图片 | 图片按桶预处理、VAE编码并写入首个条件latent；续接复用参考anchor | **选定**：生成前固定ROI，直接改变图像条件。原人物像素不重绘；保持其他输入。不是保证全片遵守构图的硬约束。 |
| ref_img_index／mask_frame_range | 续接中参考anchor相对时间位置和注意力范围；官方给出减轻重复动作的建议 | 不是手部位置或骨骼控制，也不改变首段，因此无法覆盖E1c早期手入画问题，本轮不同时改。 |
| generate_avc 条件视频 | 续接消费前段末13帧与latent，并保留参考anchor | 不是现成的单独动作驱动CLI；人为替换视频会同时涉及音频窗口、条件帧和时间映射，本轮不做未验证改造。 |
| ref_target_masks | 双说话人空间区域与音频条件路由 | 不当成手部遮罩、姿态图或骨骼ControlNet。公开单人CLI未建立这些接口。 |

选择不是“参考图必然更好”的结论。假设是：在相同声音、提示和模型下，以更紧的脸部参考减少可出现肩/手的视觉空间。固定1004方图相对1254方图约1.249倍线性近景，且会切掉部分头发/肩部；必须同时检查顶框、下巴、齿列和身份代价。若手仍出现或画面拥挤，保留负结果，不靠成片再裁掩盖。

原始图片为此前生成的虚构人物，授权和原始哈希沿用；裁切只是模型输入预处理。没有用新的生成图替代人物，没有用真人动作视频冒称同一个变量，也不证明手部解剖已修复。

可复核来源：[固定CLI](https://github.com/meituan-longcat/LongCat-Video/blob/6b3f4b8582a8bc3f20f795735f5383716c4ba794/run_demo_avatar_single_audio_to_video.py)、[固定pipeline](https://github.com/meituan-longcat/LongCat-Video/blob/6b3f4b8582a8bc3f20f795735f5383716c4ba794/longcat_video/pipeline_longcat_video_avatar.py)、[当前官方用法](https://github.com/meituan-longcat/LongCat-Video#run-longcat-video-avatar)。本地完整源码快照仅供实验复核，不加入本轮公开备份允许清单。

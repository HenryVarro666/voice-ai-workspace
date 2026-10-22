# 来源与核对范围

核对日期：2026-10-20。范围为 LongCat-Video-Avatar 1.5、OmniAvatar、HunyuanVideo-Avatar 的官方公开入口，以及本机 speech-avatar / DSH / local-speaker-lab 的接入条件。源码快照与本地文件哈希见 [source-lock.json](source-lock.json)。本轮只下载公开源码与文档文本，没有下载新模型权重、执行推理或访问远程服务器。

## 官方源码与文档

| 来源 | 固定版本／核对内容 | 事实与使用边界 |
| --- | --- | --- |
| [LongCat README](https://github.com/meituan-longcat/LongCat-Video/blob/6b3f4b8582a8bc3f20f795735f5383716c4ba794/README.md) | 默认分支提交 2026-05-27，`6b3f4b8` | v1.5、蒸馏、INT8、单/多人、续接；README 的一般视频性能不替代 Avatar 的同机测试。 |
| [LongCat 推理入口](https://github.com/meituan-longcat/LongCat-Video/blob/6b3f4b8582a8bc3f20f795735f5383716c4ba794/run_demo_avatar_single_audio_to_video.py) | 93 帧、v1.5 25 fps、13 帧条件、单段默认、vocal separation、distill 分支 | 单段 3.72 s；后续段各增加 3.20 s；蒸馏路径将 steps=8、两种 guidance=1.0。这些是代码行为，不是实测延迟。 |
| [LongCat 导出](https://github.com/meituan-longcat/LongCat-Video/blob/6b3f4b8582a8bc3f20f795735f5383716c4ba794/longcat_video/audio_process/torch_utils.py) | `save_video_ffmpeg` | 导出按视频长度裁音轨，再按音轨长度裁视频；单段不足会造成完整音频不再被保留。 |
| [LongCat 模型卡](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar-1.5) | 代码与模型权重 MIT；卡片正文核对 | 参考语音与人物素材权利独立；HF 自动生成的通用加载片段不作为 Avatar 入口依据。 |
| [vLLM-Omni 官方支持表](https://docs.vllm.ai/projects/vllm-omni/en/latest/models/supported_models/)／[recipe](https://github.com/vllm-project/vllm-omni/blob/main/recipes/meituan-longcat/LongCat-Video-Avatar-1.5.md) | 2026-10-20 文档快照；recipe Maintainer=Community | 1×H100 80GB 的离线入口；示例 93 帧 INT8/8-step，约 41.0/56.8 GiB 峰值、130/33 s 加载（CPU/GPU build）。明示 offline only、online serving 未支持。数字属于文档作者的 Modal H100 条件，不是本机测量。 |
| [OmniAvatar README](https://github.com/Omni-Avatar/OmniAvatar/blob/1536bf31abaec74364fb7d5883470d5b23ffa7f8/README.md) | 默认分支提交 2025-08-06，`1536bf3` | 1.3B/14B、LoRA 音频条件、20–50 steps、YAML 推理、A800 显存表；s/it 不能与完整视频耗时直接比较。 |
| [OmniAvatar 项目页](https://omni-avatar.github.io/) | 面部/身体、提示词动作与情绪 | 作者示例支持表情控制，不证明本项目任意中文都能准确表现情绪。 |
| [OmniAvatar 推理代码](https://github.com/Omni-Avatar/OmniAvatar/blob/1536bf31abaec74364fb7d5883470d5b23ffa7f8/scripts/inference.py)／[音频前缀函数](https://github.com/Omni-Avatar/OmniAvatar/blob/1536bf31abaec74364fb7d5883470d5b23ffa7f8/OmniAvatar/utils/audio_preprocess.py) | 默认配置 `silence_duration_s=0.3`；输入前缀与导出前缀 | 输入加 0.3 s，导出音轨加 0.3+1/fps；25 fps 时为 0.34 s。这是显式前缀，不是测得的模型 lip-sync 误差。 |
| [OmniAvatar 模型卡](https://huggingface.co/OmniAvatar/OmniAvatar-14B)／[代码许可](https://github.com/Omni-Avatar/OmniAvatar/blob/1536bf31abaec74364fb7d5883470d5b23ffa7f8/LICENSE.txt) | Apache-2.0 | Wan 基座、音频编码器及其他依赖分别核对；不能只看应用仓库一个 LICENSE。 |
| [Hunyuan README](https://github.com/Tencent-Hunyuan/HunyuanVideo-Avatar/blob/8c31d0d489df8418fa36a2a709ebdf0b47c7bf06/README.md) | 默认分支提交 2025-12-16，`8c31d0d` | 情绪/多人、FP8/offload、Gradio；原生最小 24GB 条件很慢，推荐 96GB；10GB 是另一个 Wan2GP 路径；官方 ComfyUI 计划仍未勾选。 |
| [Hunyuan 许可](https://github.com/Tencent-Hunyuan/HunyuanVideo-Avatar/blob/8c31d0d489df8418fa36a2a709ebdf0b47c7bf06/LICENSE) | Tencent Hunyuan Community License | 地域排除 EU/UK/韩国，分发标识、用途及跨模型训练约束；与 MIT/Apache 不同。这里列公开条款对选型的影响，不作个案法律结论。 |
| [HeadAudio](https://github.com/met4citizen/HeadAudio) | 实时浏览器 viseme、AudioWorklet、15 类、英语合成音训练、处理补偿 | 可作为实时嘴部分析候选；它本身不输出完整语义表情和身体动作，中文需独立评估。 |

GitHub REST API 同时查询各仓库元数据与递归文件树。三个固定快照均未见 `.github/workflows` 或明确训练启动入口；Hunyuan 的 `assets/test.csv` 是示例清单，不是自动化测试。没有据此断言作者没有内部训练/测试。默认分支最后提交日期不代表维护 SLA，star 数不计入成熟度排名。Hunyuan 一个猜测的 `scripts/run_infer.sh` 返回 404，实际入口由 README 的 `hymm_sp/sample_gpu_poor.py` 确认；该失败保留在锁文件。

## 本地证据

前一份[口型技术指南](../../reports/Avatar%20%E5%8F%A3%E5%9E%8B%E7%94%9F%E6%88%90%20%E6%8A%80%E6%9C%AF%E8%B7%AF%E7%BA%BF%20%E5%AE%9E%E9%AA%8C%E6%8C%87%E5%8D%97.md)与[原来源](../Avatar%20%E5%8F%A3%E5%9E%8B%E7%94%9F%E6%88%90%20%E6%8A%80%E6%9C%AF%E8%B7%AF%E7%BA%BF%20%E5%AE%9E%E9%AA%8C%E6%8C%87%E5%8D%97/sources.md)作为历史背景，本轮新增研究单独保存。[E1 质量报告](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/2026-10-20-e1-musetalk/QUALITY_REVIEW.md)仍为 NEEDS WORK；12 段播放、1,032 帧观察与 SyncNet 偏移估计不等于人工逐段音画签收。

本地源码的调用边界、复用位置与所需改动见 [code-map.md](code-map.md)。报告中的选型次序、接口草案、阶段预算与进入条件是工程判断和建议，尚未实施或测量。

# 当前代码到扩展方向的映射

2026-10-20 本地只读核对；代码文件的当时哈希见 source-lock.json。两个 DSH 子仓库和 local-speaker-lab 可能由其他工作继续修改，本文不是部署清单。

| 已有文件／入口 | 核对到的能力 | 可复用内容 | 接入时仍需完成 |
| --- | --- | --- | --- |
| [E0 准备](https://github.com/HenryVarro666/speech-avatar/blob/main/scripts/prepare_e0.py)、[校验](https://github.com/HenryVarro666/speech-avatar/blob/main/scripts/validate_e0.py) | 36 个合成音频的来源、哈希、家族分割与冻结；当前交叉音色 | 冻结方法与拒绝覆盖 | 新增自然中文展示开发集及显式 avatar/voice 绑定，不能覆盖旧 E0。 |
| [MuseTalk worker](https://github.com/HenryVarro666/speech-avatar/blob/main/workers/musetalk/run_e1.py) | 固定计划、共享加载、单 GPU 外部作业检查、首 PNG／完整编码计时 | 执行记录、资源隔离、失败保留方式 | 当前包装器依赖 MuseTalk 的内部函数、OmegaConf 和 cv2 埋点，不能直接换模型名。LongCat 要独立 adapter／环境。 |
| [E1 媒体分析](https://github.com/HenryVarro666/speech-avatar/blob/main/scripts/analyze_e1.py) | 全解码、输出哈希、源音轨长度／相关性、画廊 | 公共的媒体检查方法 | `EXPERIMENT`、v15 路径与页面内容写死；新实验需参数化或抽小函数，保留旧结果不覆盖。 |
| [E1 质量分析](https://github.com/HenryVarro666/speech-avatar/blob/main/scripts/audit_e1_quality.py) | SyncNet 校准、固定头像框、逐帧嘴部图 | 校准、偏移曲线、对照与审计方法 | 固定框与 mouth ROI 只适用于 E1 静止人物；完整头动需要逐帧检测／跟踪。人听评分仍需审阅页。 |
| [ReplySpeaker](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin/blob/master/src/client/voice/speaker.ts) `schedule`／`stop` | 单 AudioContext、FIFO、PCM 排程、gen、取消 reader/source | 唯一实时音频播放器与取消语义 | `subscribe()` 只有 speaking 状态，无 PCM／排程时间／外部 epoch 事件；在真实排程点增加只读观察 hook。 |
| [reply-listener](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin/blob/master/src/client/voice/reply-listener.tsx) `dhMode` | 文本切句 TTS、历史去重；数字人改走完整回复视频 | 历史不重播、turn 边界、现有普通 TTS 路径 | 现有数字人会接管音频；新 live 展示应消费已生成 PCM，不能同时触发 dhSpeak 重合成。 |
| [companion](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin/blob/master/src/client/voice/companion.tsx) | UI、预录静音任务视频、带声 DUIX 视频、视频队列与打断 | 窗口和 idle 状态、播放/取消用例 | speaking 布尔值不能驱动精确口型；离线 MP4 回放和实时 WebGL 渲染需明确模式与音频所有者。 |
| [bridge](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/bridge/voice_bridge.py) `/api/dh/speak`、`_dh_synth_segment` | 接收 text，再合成 TTS，提交 DUIX；丢弃旧任务 | 任务状态、超时、错误回退的经验 | 新实验入口先接最终 WAV/PCM 的引用，不能复制整套 ASR/LLM/TTS；discard 并不自动证明底层 GPU 推理被中止。 |
| [native server](https://github.com/HenryVarro666/local-speaker-lab/blob/main/src/speaker_lab/scheduling/server.py) `invalidate`／`on_audio` | 输出 epoch、playback_reset、原生 PCM；过期数据过滤 | 已有原生输出和取消事件 | 与 Avatar 建薄适配器，保留 24 kHz；不能把 16 kHz E0 检查硬套到在线输出。 |
| [native page](https://github.com/HenryVarro666/local-speaker-lab/blob/main/src/speaker_lab/scheduling/page.html) `audio`／`resetAudio` | 24 kHz AudioContext、输出 PCM 排程、epoch 检查 | 第二个 upstream 的播放观察点 | 浏览器播放点补同构事件；不把 server 收到 PCM 的时间当扬声器呈现时间。 |
| [DuplexLab protocol](https://github.com/HenryVarro666/local-speaker-lab/blob/main/src/speaker_lab/duplex/protocol.py)、[review](https://github.com/HenryVarro666/local-speaker-lab/blob/main/src/speaker_lab/duplex/review.py) | 哈希协议、审阅包、实际听检确认、reviewer/provenance | 设计与数据契约经验 | 不是现成的视频 MOS 组件；Avatar 新增音色/自然度/同步/表情审阅字段，首版无需复制训练、数据库和任务系统。 |

所有上游业务只消费/提供约定格式，speech-avatar 保持同级独立仓库。若将来修改插件，在主仓库镜像同步并运行既有检查；本轮没有改动这些源码。

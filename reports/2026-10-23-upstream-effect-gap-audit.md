# 上游展示效果、本地实现与现有代码差距

核对日期：2026-10-23（America/Chicago）。本轮只核对公开文档、源码、本机硬件与已有实验记录；未访问 apex/H100、安装依赖、启动推理或部署。上游 README 的两条抖音链接未能通过读取工具访问，以下不包含对演示影片画质或剪辑的直接判断。

## 判断

可以用自有机器实现上游的语音助手与分段对口型视频。当前工作区已具备语音主链路、数字人接口和浏览器播放框架；最直接的缺口是实际 DUIX 服务、角色素材及完整链路验收。

本轮 GitHub API 核验：上游 main 为 `480bbabada7335735cad591eaa55f32fe54a4214`，与原 DSH 源码仓库 HEAD 相同。原目录还有大量后续本地修改，因此不属于“缺了上游新版本功能”。公开纯源码备份的提交编号与原仓库不同，不应用两者 SHA 是否相同判断功能差距。

## 上游的效果由什么组成

| 效果 | 实现 | 对复现的含义 |
| --- | --- | --- |
| 听、回答、克隆声音、插话 | ASR → DSH/LLM → TTS → 浏览器播放 | 已有本地工程基线；无需为了头像重新训练 ASR/LLM |
| 待机时人物在动、说话时切换动画 | 预录素材与播放状态切换 | 身体动作可以来自素材；这种动画不随当前语音产生准确嘴形 |
| 当前回复对应的嘴形 | TTS 音频 + 形象视频 → DUIX → 带音轨 MP4 → 播放 | 需要真实视频后端；已有接口或替身不等于已生成真实口型 |
| QQ 文本/语音推送 | NapCat/OneBot | 可选渠道，与本地数字人效果无必然关系 |

上游称为“流式”的部分是分段视频流水线：先完成助手文本、分段合成音频，再生成各段视频。下一段 TTS 可与当前段视频生成重叠。它不是逐帧即时视频通话。

尤其不能把 README 开头的“0.5 秒开口”当成数字人模式指标。同一 README 的数字人章节记录 7.3 秒音频生成视频由 20.1 秒降到 14.1 秒，且明确视频完成后才带声音播放。DUIX 官方也将此开源 Avatar 项目定位为非实时视频合成。上述数字是作者记录，不是本轮复测；拼接好的演示视频也不能证明真实等待时长。

来源：[上游 README](https://github.com/beiyege-01/dsh-voice-ai-girlfriend/blob/480bbabada7335735cad591eaa55f32fe54a4214/README.md)、[DUIX 官方说明](https://github.com/duixcom/Duix-Avatar#7-how-to-interact-in-real-time)。

## 当前工作区已有与缺少的部分

| 部分 | 已有证据 | 尚缺什么 |
| --- | --- | --- |
| 语音对话 | FunASR + 本地 Qwen3.5 9B + Qwen3-TTS 0.6B 已在 apex 跑过 | 真人麦克风、耳机/外放 AEC、长会话验收；不能以合成输入代替 |
| 陪伴窗口 | 待机素材、静音说话动画、拖动缩放；原目录保留背景媒体 | 人设、音色、待机和形象素材的一致配置；普通说话素材需自备 |
| 数字人后端适配 | `/api/dh/speak`、分段合成、submit/query、队列、历史、停播与失败回退 | 最近部署记录仍为真实 DUIX 未部署；本轮没有刷新在线状态 |
| 数字人配置 | 示例已列出服务、共享目录、角色视频、开关 | 示例 `enabled=false`、`avatar_video` 为空；必须填实际路径并核验服务 |
| 部署可移植性 | 保留上游 Compose 与 Windows 启动器 | Compose 仍挂载 `d:/...`；Linux 要改目录；实际宿主端口是 9000，非旧注释的 8383 |
| 跨机器数字人 | `duix_base` 可指定服务地址 | 当前请求只传音频/视频裸文件名，输出也从本地 temp 读；远程后端还需要共享目录或明确的上传/下载适配，仅改 URL 不够 |
| 独立 Avatar 实验 | speech-avatar 已跑 MuseTalk/LongCat 离线视频；E1d 构图实验正在进行 | 尚未接入 DSH；现有视频质量仍 NEEDS WORK，人工音画验收未完成 |
| 低延迟真人对话头像 | 已有 AudioContext 播放、取消与任务失效机制可复用 | 对最终输出音频的同步展示接口、音画共同时钟、实时帧/嘴形输出、过期帧清理与真人验收 |

代码依据：

- [reply-listener.tsx](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin/blob/master/src/client/voice/reply-listener.tsx)：DH 就绪判定、等待 settled 回复、排除重复普通 TTS。
- [companion.tsx](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin/blob/master/src/client/voice/companion.tsx)：静音预录层与带音轨 DH 视频层分离，分段队列与停播。
- [voice_bridge.py](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/bridge/voice_bridge.py)：`_dh_synth_segment`、`_dh_submit_and_wait`、文件名协议与生成流水线。
- [配置模板](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/bridge/bridge-config.example.json)、[Compose](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/bridge/docker-compose-5060ti.yml)、[安装说明](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/docs/SETUP.md)。
- [语音实验入口](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/README.zh-CN.md)、[Avatar 当前记录](https://github.com/HenryVarro666/speech-avatar/blob/main/PROJECT_STATUS.md)。

语音链路现有 17 轮合成输入测量：新会话首次 3.75 秒，16 热轮 1.04–2.01 秒；起点为输入最后有声采样，终点为浏览器 AudioContext 首有声排定，不含硬件、真人/AEC，也不是严格冷启动。speech-avatar 的 LongCat E1c 两段整进程约 263–267 秒（含加载及生成/编码）；它适合当前离线视觉探索，不能作为已实现实时聊天的证据。

## “本地运行”的两种含义

本轮只读检查确认当前 Mac 是 M4 Pro、24 GiB 内存。它可以承担浏览器、控制和预览；上游 NVIDIA/CUDA/TensorRT 容器不能原样迁移到这台 Apple Silicon 机器。要全部在 Mac 上推理，需要另外选择并验证兼容 ASR、TTS、LLM 和头像方案，目前没有相同效果和速度的本机验收证据。

如果本地是指“自有 GPU 机器运行、Mac 打开网页”，现有 apex 路线已满足语音部分的自托管方向。模型和资源预先下载、本地 LLM 接入后，不要求使用云端对话或数字人 API；涉及 QQ 等外部渠道时仍需网络。DUIX 官方提供 Windows/Ubuntu 部署路线，推理依赖 NVIDIA。

apex 是 16 GB RTX 5080；此前语音全栈加载快照约 12.6 GB，上游估算 DUIX 还需 4–6 GB。这只能说明不能直接假设可同时常驻，不能当作今天的显存测量。部署前需重新核验资源，比较分卡/分机或分时加载方案。保留 Qwen3-TTS 即可测试 DUIX：当前桥接的数字人路径已经支持该 TTS，不必为了复现画面换回 OmniVoice。

## 建议推进顺序

1. **先复现一段真实口型。** 在独立 NVIDIA 环境准备 DUIX，只用一条已确认的短 WAV 与一段形象参考视频，验证真实生成、输出音轨、完整解码和肉眼接受，测首段等待与生成耗时。避免一开始同时引入 ASR/LLM 和新音色。
2. **接回已有数字人适配。** 统一宿主路径/卷、9000 端口、角色素材、文件交换和开关。跨机器时先补传输契约；不要以服务可达替代文件可用。
3. **完成一轮浏览器验收。** 检查一段和多段回复、超时纯语音回退、插话停播、过期视频不重播、重复刷新，以及真实后端是否继续耗算力。停播和取消推理分开记录。
4. **根据体验决定产品路线。** 目标是上游式写实口播展示，则继续优化此分段链路；目标是自然视频聊天，则保留现有快速语音，另做随音频驱动的实时头像，不应把慢视频生成加到每轮首声之前。

后一条可先用浏览器角色 rig + [HeadAudio](https://github.com/met4citizen/HeadAudio) 这样的音频驱动嘴形候选，复用同一音频时间轴；角色、中文嘴形、表情及附加延迟仍需独立验证。它是可探索的实时动画路线，写实外观与上游视频方案不同。

MuseTalk/LongCat 的离线画质支线继续留在 speech-avatar；DuplexLab 的 ASR 训练支线不构成复现此展示的前置条件。当前最有信息价值的下一项是“真实 DUIX 单段效果/耗时验证”，而不是再训练一轮 ASR 或直接重写整套前端。

本轮未修改运行代码，未运行新性能测试，也未提交、推送或部署；以上步骤为建议，尚未执行。

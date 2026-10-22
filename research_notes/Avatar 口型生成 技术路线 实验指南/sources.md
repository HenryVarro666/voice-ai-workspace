# Avatar 口型方案来源核对

日期：2026-10-20，America/Chicago。对应[技术指南](../../reports/Avatar%20%E5%8F%A3%E5%9E%8B%E7%94%9F%E6%88%90%20%E6%8A%80%E6%9C%AF%E8%B7%AF%E7%BA%BF%20%E5%AE%9E%E9%AA%8C%E6%8C%87%E5%8D%97.md)。本文件记录选型事实与推论的区别，不包含新运行结果。

## 本地依据

- PROJECT_STATUS 与最新原生全双工预约方案：主展示改为预约 Agent；既有中文 DSH 与新英语主线分开。
- speaker.ts：当前 PCM 调度直接连接 destination；有 generation counter，但没有音素/viseme 事件。
- reply-listener.tsx：DUIX 模式消费 settled 助手文本并替换普通逐句 TTS。
- voice_bridge.py：DUIX 请求由文本整段合成 WAV 后提交文件，不能原样复用为原生模型 PCM 的旁路渲染。
- companion.tsx：普通 task 视频静音轮播；DUIX 分段视频带音轨。两种能力分开。

## 官方来源

| 来源 | 支持的事实 | 不能据此推断 |
| --- | --- | --- |
| [HeadAudio README](https://github.com/met4citizen/HeadAudio) | AudioWorklet、MFCC/Gaussian 分类、Oculus viseme；英语合成声音训练；作者提示精度限制与 50–100 ms 补偿 | 当前中文音色、真实麦克风或 PersonaPlex 输出已达标 |
| [HeadAudio LICENSE](https://github.com/met4citizen/HeadAudio/blob/d3af5f9ff86ab6b2b1913d411a4e1922ec101953/LICENSE) | 代码 MIT | 其附带所有角色/媒体都可任意再分发 |
| [MuseTalk README](https://github.com/TMElyralab/MuseTalk) | 1.5 入口、人物准备、作者 V100 吞吐；代码/模型/第三方/素材分别说明 | RTX 5080 上的首帧、显存、共驻和端到端延迟 |
| [MuseTalk realtime 源码](https://github.com/TMElyralab/MuseTalk/blob/0a89dec45a0192b824e3cf4daf96c239440c5ed8/scripts/realtime_inference.py) | inference 接 audio_path，先提取音频特征；按配置 audio_clips 循环 | 已有接受任意到达 PCM 并保证因果出帧的在线服务 |
| [DUIX Avatar README](https://github.com/duixcom/Duix-Avatar) | 非实时生成定位、Docker、easy 文件提交/查询接口 | Mobile SDK 实时能力等于本 bridge 的容器能力 |
| [DUIX LICENSE](https://github.com/duixcom/Duix-Avatar/blob/1328feb5871448c8fa3d0e45b3bbc87e7c1d458a/LICENSE) | 当前为社区协议；与 README 的门槛措辞有差异 | 继续沿用历史笼统的免费商用描述 |
| [Duix Mobile](https://github.com/duixcom/Duix-Mobile) | 原 GuijiAI/duix.ai 链接重定向到移动 SDK | 与服务器 Avatar 为同一产品/相同计时条件 |
| [Rhubarb README](https://github.com/DanielSWolf/rhubarb-lip-sync) | 文件音频到带时间 mouth cue；PocketSphinx 英语、phonetic 非英语入口 | 中文预测精度、低延迟在线部署 |
| [VRM 表情规范](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/expressions.md) | 五元音预设可选，自定义与 override 规则 | 任意 VRM 都有完整闭唇/咬唇形状 |
| [three-vrm API](https://pixiv.github.io/three-vrm/docs/variables/three-vrm-core.VRMExpressionPresetName.html) | 表情预设名 | 内置音频到嘴型预测器 |
| [Audio2Face SDK](https://github.com/NVIDIA/Audio2Face-3D-SDK/blob/main/docs/README.md) | 音频可累积后流式执行，结果回调；CUDA/TensorRT | 当前 apex 可共驻或到目标 Avatar 的映射已完成 |
| [Wav2Lip README](https://github.com/Rudrabha/Wav2Lip#non-commercial-open-source-version) | 原版非商业/研究个人使用说明 | 新产品可直接忽略用途条件 |
| [Web Audio 规范](https://webaudio.github.io/web-audio-api/#dom-audiocontext-getoutputtimestamp) | contextTime 与 performanceTime 的对应关系 | 单靠 rAF 就测到物理显示/声音延迟 |

## 本文的设计判断

独立小仓库、浏览器实时优先、MuseTalk 离线视觉验证、DUIX 兼容保留，以及 E0–E5 的规模、阈值与时间盒，均为基于项目约束的设计建议；不来自上述作者的性能承诺。没有下载或运行第三方代码。远端 revision 见指南的版本表，私有配置与凭据未读取或保存。

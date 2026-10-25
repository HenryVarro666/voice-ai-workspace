# Experiment map / 实验地图

The README describes intended products. This map identifies which experiment changed a decision and where to inspect its evidence. Full technical history is preserved separately in EVOLUTION.md; historical "not published" statements describe the time of that record.

| Workstream | Main question | Current decision | Detailed index |
|---|---|---|---|
| Chinese assistant | Can natural speech, endpointing and interrupted playback remain reliable on one GPU? | Retain measured baseline; isolated cancellation repair needs sender deadlines and deployment acceptance | [DSH decisions](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/docs/EXPERIMENT_INDEX.md) |
| Browser interaction | Can capture, sentence state and scheduled audio avoid stale/repeated results? | Offline core contracts exist; host, microphone and hardware acceptance remain separate | [Plugin methods](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin) |
| Appointment agent | Can the latest requested slot be correctly spoken and confirmed after interruption? | Cached1.552s prototype retained;0.898/0.868s candidates rejected | [Scheduling studies](https://github.com/HenryVarro666/local-speaker-lab/blob/main/docs/EXPERIMENT_INDEX.md#interactive-scheduling) |
| DuplexLab | Does curated or weighted training improve speech content retention? | Multiple frozen studies do not establish a reliable overall gain | [ASR studies](https://github.com/HenryVarro666/local-speaker-lab/blob/main/docs/EXPERIMENT_INDEX.md#duplexlab-matched-budget-asr-studies) |
| Avatar | Can offline portraits preserve clear speech with natural expression? | LongCat offline candidate/MuseTalk baseline; E1c prompt-only and E1d tighter-reference trials did not establish a fix | [Avatar stages](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/INDEX.md) |
| Avatar async E2 | Can12new voice utterances generate/play safely in an isolated single-user loop? |12new videos/1152frames; two12-play rounds,7unit/9backend/13browser checks; CPU98.474–266.092s; new-input sync/human AV remain unaccepted | Local measured results — local-only artifact: `../speech-avatar/experiments/2026-10-24-e2-async-single-user/RESULTS.md` / runbook — local-only artifact: `../speech-avatar/experiments/2026-10-24-e2-async-single-user/RUNBOOK.md` |

## Reading a record

1. **Question and method:** what changed, what was held fixed, which product failure it addresses.
2. **Evidence:** sample counts, split exposure, code/model revisions and timing endpoints.
3. **Decision:** adopted, candidate only, rejected or inconclusive. An experiment may succeed technically while its proposed method is rejected.
4. **Next gate:** a concrete check required before integration or another expensive run.

Exact numeric summaries are public where approved; raw audio/video, full transcript review pages, credentials, weights and runtime logs remain local. Local-only links are converted to readable artifact references. Aggregate recomputation may be possible without media; fresh model/quality reproduction still requires the original inputs and permissions.


## 2026-10-25 E5b：CUDA路径已准备，GPU对照待空闲资源

[本轮记录](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/2026-10-25-e5-gpu-comparison/RESULTS.md)：固定同模型/revision/参数/4文本/12帧分块/24kHz协议，新增显式CUDA/UUID资源保护和独立后端选择。分配前GPU1已被其他任务占用，GPU推理0次；速度/停顿改善和GPU恢复验收均未完成，不能以41项本地测试替代实卡验收。新CPU路由9实际请求：7完整/1播放中取消/1断流incomplete；显式重试、新句恢复与旧错误丢弃通过，7PCM/hash/样本/code检查通过。首PCM3.040–4.471s、RTF3.088–3.571、最大计划间隙2.696s，CPU性能门槛仍未过。

[独立预览49917](http://127.0.0.1:49917/index.html)；原50451保留。新GPU入口只在无其他计算PID、空闲且完成自有上下文复查后使用；未操作apex/共享包/其他进程。独立H100最近资源核验2026-10-25；841旧冻结记录不变。下一步等空闲卡，GPU预热后执行4句交叉主对照和7请求恢复；真人麦克风/ASR/翻译/人工AV/部署均未验收。用户授权本轮审查后源码/元数据公开备份，推送回执另记。


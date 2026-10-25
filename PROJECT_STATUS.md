# Current project state / 当前状态

## 2026-10-24 Avatar actual TTS streaming

[Speech Avatar E5a](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/2026-10-24-e5-live-tts/RESULTS.md) connects fixed Qwen3-TTS presets to actual single-player scheduling in an independent instance.7browser calls yield5complete/4newChinese texts,1controlled barge-in cancellation and1properlyincomplete transport drop; explicit recovery/stale rejection pass. FirstPCM3.133–5.363s, plannedstart3.183–5.415s, CPU RTF3.135–3.591/maxgap2.840s: lifecycle substage passes, realtimeperformance does not.36tests pass. Actual microphone/ASR/translation/humanAV/production remain pending. This user authorized reviewed source-only publication; no rawvoice/model/vendor/credentials or original Git history are exported.

## 2026-10-24 Avatar realtime interface pilot

Speech Avatar adds a local idle/RMS/HeadAudio comparison using one actual DSH playback clock and optional fault-isolated schedule observations.12complete fixture comparisons retain exact sample counts;10local fault/recovery checks pass. Planned audio start51.6–81.9ms, first active pose78–206ms after planned audio start, rollingrAFP95 8.8–9.3ms; physical/live upstream latency unmeasured.27avatar/13plugin tests plus typecheck/build pass. Local GPU drawing is an approximate portrait prototype; live ASR/translation/TTS, human Chinese AV acceptance, dedicated neural GPU benchmark and deployment remain pending. [Results](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/2026-10-24-e2-e5-realtime/RESULTS.md).

Coordination snapshot updated:2026-10-23, America/Chicago. Experimental records retain their own measurement dates. This is the public coordination snapshot. Private operational/career notes and original media remain outside public repositories. Publishing source does not deploy it.

| Direction | Completed evidence | Still open |
|---|---|---|
| DSH Chinese assistant | Measured baseline; latest cancel-recovery isolated36HTTP/8player stops | Sender-stall deadline, lock budget, M0compatibility/replacement recovery, microphone/AEC |
| Native booking | Cached native readback1.552s median; versioned simulated booking/reschedule | Faster candidates rejected after date/actual-entry failure; real microphone and human quality acceptance |
| DuplexLab | Latest12fresh models,4arms×3seeds;test362,MER9.7315/9.8353/9.8353/10.1329% | No reliable overall weighting/selection gain; padding save/load and mixed-length input contracts next |
| Avatar | E1c6local sync variants+2new videos;15CPUtests recorded | NEEDS WORK;human sync/video scores pending;tail generation gate not met |

The latest remote health snapshots belong to their dated experimental reports. This publication performs local checks only and does not claim newly verified GPU availability or unchanged remote services.

Public sources and bilingual overviews are held in five repositories. See README.md for the product goals, EXPERIMENTS.md for decision-level evidence and PUBLICATION.md for backup exclusions. Historical logs retain original timing and deployment qualifiers.


## Public backup receipt

All five repositories are public under HenryVarro666. Initial remote recursive trees and rendered README content were verified; code revisions are pinned in REPOSITORIES.json. The plugin preserves its upstream fork, while the DSH bridge excludes upstream video-bearing history.

Local Speaker Lab gained a Windows-only tzdata dependency and byte-stable patch fixtures after the first public CI. Its Linux lock invariant evaluates the Linux target; three native POSIX deployment-tool tests are excluded from Windows checks. Linux still executes the strict patch/hash tests. Local rerun:636pass/4skip/22subtests; the current remote Actions run is the authoritative cross-platform result.

Source backup scope and manifests are in PUBLICATION.md. The original experiment worktrees and private media remain local; the editable public checkouts are separate. No services or GPU processes were changed.


Final cross-platform verification: DSH bridge and browser-plugin GitHub CI passed. Local Speaker Lab run39734116968 passed Windows/Ubuntu Python3.11/3.12 and full Linux integration, with the documented POSIX-only deployment-tool scope.989local/cross-repository links passed; final exact-index credential scan introduced no unreviewed finding.328original frozen metadata/source files remained byte-identical. Code commits are pinned in REPOSITORIES.json.


## Repeatable backup workflow / 可重复备份

The original working folders remain the development locations. `backup_public.py preview` builds isolated candidates for all five public repositories, `show <plan-id> --diff` reviews the contents, and `push <plan-id>` requires an exact confirmation after displaying the list again. Credentials, weights, audio/video and runtime files stay excluded. Public coordination summaries are maintained explicitly in public_docs. The helper preserves curated remote changes, blocks stale/conflicting plans and records verified push receipts. See [instructions](PUBLIC_BACKUP.md). Preparation on 2026-10-22 used local bare remotes and a read-only preview; those preparation checks did not publish the helper.


## 2026-10-23 Backup-tool release / 备份工具发布

This release adds the repeatable backup helper, its five-repository configuration, exact-context non-secret exception list, integration tests and maintenance guide to the documentation hub. The user explicitly authorized a fresh preview, exclusion review and publication. All 16 backup integration tests were rerun successfully on 2026-10-23; they exercise local bare remotes, stale-plan/conflict rejection, source-history isolation, exclusions and interrupted-push recovery. Each candidate is reviewed and scanned before pushing; publication receipts record the exact remote revisions. Unchanged code repositories retain their existing commits. The hub and Speech Avatar use explicit public-summary overrides; concurrent new Avatar experiment code and live logs are outside this release. No GPU, speech-model or production-service validation is implied.


## 2026-10-23 Avatar reference-framing result

Speech Avatar completed two fixed-ROI reference-input renders against E1c parents, with the same accepted audio, prompt, seed and model. Exact source pixels and actual conditioned audio payloads were retained. Face-box area increased26.62%→41.22% /27.07%→42.49%, but hand entry, emphasized articulation and teeth issues remain; tighter headroom is a tradeoff. The change is not adopted as a hand/expression fix. Complete processes271.001/264.656s include loads; these are offline experiments, not conversation latency.18CPUtests,2decode/audio checks,258single-face frames and4browser playbacks pass; human AV acceptance pending. Next verify explicit motion/driving-video or rig interfaces before more inference. No production/apex change or publication in this experiment.


## 2026-10-23 E1d review recovery

Completed videos were preserved and the local preview gained draft feedback export. Framing preference and explicit audiovisual acceptance are independent; defaults stay unreviewed, the export binds frozen clip hashes, and human records are never auto-filled.22CPUtests and4fresh browser playbacks pass; actual downloads, reveal, single audio and clean delivery were checked using isolated QA fixtures. No new render, model/service change or apex access; E1d remains NEEDS WORK and human acceptance pending.


## 2026-10-23 E1f-R男女分区动作对照完成

先核对显式控制接口，选LivePortrait原生模板分区：头姿/非眼表达0.65、眼区1.0、global1.0，复用原头像/已接受配音/E1c驱动。男女各attempt1成功，原生worker856.164/371.437s；共享CPU亲和性不同，见资源修订，不作速度排名。2片1254²/25fps、258单脸帧/原PCM母版通过；旧片/评分保留。深闭眼与轻头动/嘴幅可共存，下沿未见手部；牙齿仍软、末帧略张口和模型同步偏移未修，NEEDS WORK/人工接受null。[结果](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/2026-10-23-e1f-regional-motion/RESULTS.md)。

[本地四段预览](http://127.0.0.1:54462/index.html)；本轮独立目录2026-10-23-e1f-regional-motion，和另项E1f-independent-blink互不覆盖。[每步进展总账](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/PROGRESS_LEDGER.md)汇总问题→改动→证据→决定；早期格式不同，主要步骤/失败有记录，不声称完整逐命令历史。无apex、共享环境/服务改动、GPU推理、子代理、暂存/源码提交或推送。公开备份仅preview/diff。

E1f-R verification2026-10-23:26CPU tests,9script compiles,4browser endings/served hashes,258paired eye/mouth/lower-edge frames,29full/15native frames and4known nonzero sync controls pass. Source PCM exact,197locked parent files unchanged;human AVpending,NEEDS WORK. Noapex/shared-service restart/GPU inference/source commit/push.

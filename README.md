# Voice AI Workspace

**English** · [简体中文](README.zh-CN.md)

**Building voice agents that can be interrupted, keep the latest intent, and say the right facts aloud.**

This is the documentation hub for four related code repositories. It connects product goals to experiments and decisions. The projects are research and engineering prototypes; deployment, automated checks and human acceptance are reported separately.

## Problem and intended experience

A useful voice assistant must do more than produce a quick first audio chunk. It must hear a correction while speaking, cancel obsolete work, preserve names and numbers, and confirm the latest requested action. Optional avatar video must preserve that same speech clearly.

The main showcase is a simulated appointment assistant: request a slot, interrupt with a correction, explicitly confirm, then reschedule the same booking. A Chinese desktop assistant provides a separate engineering baseline. No real calendar or clinical system is connected.

## Projects and methods

| Project | Intended use | Methods | Current stage |
|---|---|---|---|
| [DSH voice bridge](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend) | Chinese voice access to a tool-capable desktop assistant on one consumer GPU | FunASR → text endpointing → DSH/local 9B → Qwen3 streaming TTS | Base chain exercised; cancellation candidate remains separate from deployment |
| [DSH browser plugin](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin) | Continuous capture, spoken replies and interruption in the DSH browser UI | Bounded pre-roll, stable sentence splitting, PCM scheduling and cancellation | Standalone build and CPU regressions; full host and microphone acceptance pending |
| [Local Speaker Lab](https://github.com/HenryVarro666/local-speaker-lab) | Interruptible booking demo and auditable speech-data research | PersonaPlex plus versioned simulated tools; DuplexLab ASR selection/SFT; glossary and two-speaker workflows | Booking prototype and offline experiments; factual speech and real-user testing still limit adoption |
| [Speech Avatar](https://github.com/HenryVarro666/speech-avatar) | An expressive speaking portrait for a future voice interface | MuseTalk/LongCat offline rendering, sync diagnostics and controlled comparisons | Videos generated; visual quality gate remains NEEDS WORK |

## What the evidence supports

| Question | Observed result | Decision and boundary |
|---|---|---|
| Can Chinese speech traverse a real assistant UI? | Latest 17-turn synthetic-input run: first session request 3.75 s; warm turns 1.04–2.01 s | Speech-end → browser scheduled first voiced output; excludes hardware, real microphone and controlled cold start |
| Can cancelled TTS stop wasting queued inference? | Before-first-PCM consumer-close → generation-exit median 1948.4 → 63.3 ms in an isolated candidate | Continue cancellation work; this is not general first-response acceleration or a production deployment |
| Can native booking readback be faster? | Accepted cached prototype: tool update → first voiced gateway PCM median 3.338 → 1.552 s, ten updates | Keep this baseline; it excludes recognition, tool-query wait and audio hardware |
| Is sub-second booking readback ready? | Prefill 0.898 s failed a date guard; later 0.868 s pacing candidate retained a human-confirmed wrong/unclear date | Reject both candidates; computational parity and ASR checks do not replace human factual clarity |
| Does selected or weighted ASR training improve retention? | Latest four-arm/three-seed pilot: MER 9.7315 / 9.8353 / 9.8353 / 10.1329% on 362 clips | No reliable selection/weighting benefit; native/uniform controls match under measured batch-1 conditions |
| Can prompts alone fix avatar expression? | E1c generated two controlled-prompt videos plus six local sync derivatives; hands and emphasized articulation persist | NEEDS WORK; conditional tail generation skipped; human AV acceptance pending |
| Can a tighter input reference constrain avatar actions? | E1d generated two fixed-ROI reference videos with the same audio/prompt/seed/model; hands and emphasized expressions remain | Framing changed, but no hand/expression fix established; 18 CPU tests pass; human AV acceptance pending |
| Can mouth timing and endings improve while preserving blinks? | E1g — local-only artifact: `../speech-avatar/experiments/2026-10-24-e1g-mouth-sync-tail/RESULTS.md`: mouth-only80ms delay,0.48s silent ending; offset -80→0ms and6/6closed tail frames, blinks/AAC exact | Familiar-clip candidate; confidence decreases, human AV/new-phrase validation pending; no service change |
| Can oral texture improve without losing current motion/sync? | E1h — local-only artifact: `../speech-avatar/experiments/2026-10-24-e1h-oral-detail/RESULTS.md`: light unsharp modestly stronger; bounded GFPGAN not superior; eyes/lips/tail/AAC exact, sync0ms | Keep model restoration off; user retained the original unsharp clip; new-input synchronization/acceptance is separate |

These rows use different datasets and timing boundaries. They must not be combined into a single speed or quality score. Full protocols, failures and uncertainty are linked from the [experiment map](EXPERIMENTS.md).

<!-- e2-async-trial -->

The user retained the exact E1h light-unsharp clip. The independent new-audio asynchronous trial — local-only artifact: `../speech-avatar/experiments/2026-10-24-e2-async-single-user/RESULTS.md` now completes12new Serena utterances and12genuine MuseTalk mouth videos:1152frames,40.32s source speech, source-exact PCM masters and closed endings. Two complete12-video browser rounds,7process tests,9real backend checks and13browser checks pass. CPU worker98.474–266.092s (median140.119s), sampled process-groupRSS7.050–7.149GiB; no CUDA. Actual cancellation exits its owned group in0.228s and a99.426s fresh recovery reproduces the original hash. Sync generalization remains unaccepted: only8/20shift controls recover,2short clips are skipped, and human AV is pending. This fixed12-utterance trial remains separate from realtime/upstream integration and existing services.

<!-- /e2-async-trial -->

## How experiments are recorded

1. **README:** the product question, selected approach, strongest supported result and next decision.
2. **Experiment index:** one row per hypothesis, with comparison, result, adoption decision and links.
3. **Detailed record:** frozen plan, source/model revisions, inputs and counts, results, failures, verification and limitations. Later reports supersede conclusions explicitly; old records remain historical.

Public repositories include source, synthetic metadata, aggregate measurements and diagrams. Credentials, weights, raw/generated audio-video, full private transcripts and runtime logs stay local. [Publication scope](PUBLICATION.md) distinguishes published evidence from local-only artifacts.

## Next work

- Make TTS cancellation bounded under a stalled sender, then verify compatibility and replacement/recovery before deployment.
- Resolve booking startup-word/date clarity against a frozen actual-entry regression before further latency optimization.
- Freeze tokenizer save/load and mixed-length batch contracts before another ASR training study; inspect reference/acoustic disagreements on train/dev first.
- Review the12new asynchronous avatar clips with a human, resolve new-input synchronization, then measure an independent exclusive-GPU path before live upstream integration.
- Validate natural microphone input, headphones and loudspeaker echo separately from synthetic trials.

## Back up while developing in the original folders

Run `python3 backup_public.py preview`, review `python3 backup_public.py show <plan-id> --diff`, then use `python3 backup_public.py push <plan-id>`. Push displays the change list again and requires the exact `PUSH <plan-id>` confirmation. The helper updates five independent public histories from reviewed source changes; credentials, weights and audio/video stay excluded. Public coordination summaries come from `public_docs/`; full local logs remain in the original workspace. See [backup instructions](PUBLIC_BACKUP.md) for scope, new experiment reports and recovery. This adds a manual backup tool; it does not schedule uploads.

## Reading order

[Repository commits](REPOSITORIES.json) · [Backup maintenance](MAINTAINING.md)

[Current state](PROJECT_STATUS.md) → [experiment map](EXPERIMENTS.md) → [roadmap](ROADMAP.md) → [historical technical log](EVOLUTION.md). Each code repository owns its installation instructions and detailed evidence.

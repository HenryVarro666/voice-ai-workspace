# Experiment map / 实验地图

The README describes intended products. This map identifies which experiment changed a decision and where to inspect its evidence. Full technical history is preserved separately in EVOLUTION.md; historical "not published" statements describe the time of that record.

| Workstream | Main question | Current decision | Detailed index |
|---|---|---|---|
| Chinese assistant | Can natural speech, endpointing and interrupted playback remain reliable on one GPU? | Retain measured baseline; isolated cancellation repair needs sender deadlines and deployment acceptance | [DSH decisions](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend/blob/main/docs/EXPERIMENT_INDEX.md) |
| Browser interaction | Can capture, sentence state and scheduled audio avoid stale/repeated results? | Offline core contracts exist; host, microphone and hardware acceptance remain separate | [Plugin methods](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin) |
| Appointment agent | Can the latest requested slot be correctly spoken and confirmed after interruption? | Cached1.552s prototype retained;0.898/0.868s candidates rejected | [Scheduling studies](https://github.com/HenryVarro666/local-speaker-lab/blob/main/docs/EXPERIMENT_INDEX.md#interactive-scheduling) |
| DuplexLab | Does curated or weighted training improve speech content retention? | Multiple frozen studies do not establish a reliable overall gain | [ASR studies](https://github.com/HenryVarro666/local-speaker-lab/blob/main/docs/EXPERIMENT_INDEX.md#duplexlab-matched-budget-asr-studies) |
| Avatar | Can offline portraits preserve clear speech with natural expression? | LongCat offline candidate/MuseTalk baseline;E1c prompt-only gate not met | [Avatar stages](https://github.com/HenryVarro666/speech-avatar/blob/main/experiments/INDEX.md) |

## Reading a record

1. **Question and method:** what changed, what was held fixed, which product failure it addresses.
2. **Evidence:** sample counts, split exposure, code/model revisions and timing endpoints.
3. **Decision:** adopted, candidate only, rejected or inconclusive. An experiment may succeed technically while its proposed method is rejected.
4. **Next gate:** a concrete check required before integration or another expensive run.

Exact numeric summaries are public where approved; raw audio/video, full transcript review pages, credentials, weights and runtime logs remain local. Local-only links are converted to readable artifact references. Aggregate recomputation may be possible without media; fresh model/quality reproduction still requires the original inputs and permissions.

# Product and evidence roadmap / 产品与证据路线

Updated2026-10-22. These are proposed next gates, not achieved outcomes.

| Sequence | Work | Completion evidence |
|---|---|---|
|1|Preserve five source/document repositories independently|Reviewed public manifests, no credentials/weights/raw media, bilingual overview, verified remote commit IDs|
|2|Bound cancelled/stalled TTS work|Sender deadline and request lock budget; thread actually exits before lock release; isolated compatibility/recovery|
|3|Make appointment facts clear at the actual entry|Freeze known wrong/unclear-date regression; all facts verified from audio; accepted voice behavior retained|
|4|Validate natural voice use|Separate headphone/microphone and loudspeaker/AEC cases; correction onset, false interruption and end-to-end hardware timing|
|5|Stabilize ASR experiment contracts|Saved/loaded tokenizer padding and mixed-length input equivalence checked; train/dev reference review before new unseen test|
|6|Improve avatar quality under a bounded hypothesis|Human sync comparison, then one stronger motion/framing condition; no tail generation before motion gate passes|

DSH keeps its own M0→M1→M2 compatibility/measurement/human-voice dependencies. Offline ASR and avatar experiments can proceed independently; they do not certify a deployed real-time product. Production replacement remains a separate operation from GitHub publication.

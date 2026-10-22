# DuplexLab Implementation Plan

> **归档副本，勿按零进度重做：** 已迁入[主仓库实施计划](https://github.com/HenryVarro666/local-speaker-lab/blob/main/docs/superpowers/plans/2026-10-20-duplexlab-implementation.md)。2026-10-20 已建立 feat/duplexlab，实施离线切片并运行 20 条真人开发录音；准确任务状态与待办只在主仓库副本维护。下面保留初版任务描述与原始复选框，不代表当前全部未执行。无明确要求不启动子代理、提交或推送。

**Goal:** 在既有 local-speaker-lab 中交付可回听、可审阅、可导出训练数据的语音实验，再完成流式识别和有对照的 ASR 微调。

**Architecture:** 保留 speaker_lab 包和原双人/词表工作流，新增 speaker_lab.duplex。CPU 数据与审阅层独立于模型进程，离线复用 WorkerRunner，流式另接 vLLM 常驻进程。模型和原始数据保留本地，公开结果只带有权分发的示例和汇总。

**Tech Stack:** Python 3.12、现有 NumPy/SciPy/SoundFile、SQLite、JSONL/TOML、静态 HTML；模型层为固定 Qwen3-ASR，合成为可选提供方适配。

**Spec:** [DuplexLab 技术设计](../specs/2026-10-20-duplexlab-design.md)。先读全部设计，再执行本计划。

## Global Constraints

- 主仓库为 HenryVarro666/local-speaker-lab；包名 speaker_lab 不变，新增目录 src/speaker_lab/duplex/。
- 规划本地路径 /path/to/projects/local-speaker-lab，本轮尚未克隆；若已存在就先核对，不覆盖。
- 本机开发使用 /opt/homebrew/bin/python3.12；不使用当前默认 Python 3.15.0rc3 建环境。
- 两份历史 ASCEND 冻结协议与运行不修改；725 条任务状态未核实，不自动另跑。
- CPU 测试、CLI 帮助和模块 import 不下载权重、不启 CUDA；GPU 环境独立且只用可用资源窗口。
- 不自动提交或推送；不影响 apex 的其他服务；API 默认关闭且费用预算为 0。
- 每个模型实验绑定输入、配置、源码、模型版本和运行状态；只完成 smoke 时如实标为 smoke。
- 新增 CLI 以下均是未来接口，完成对应任务与测试之前不能直接当作已可用命令。

## Review Focus

1. 音频路径遍历、符号链接越界、哈希变化或重复 ID：在模型启动前拒绝，任务 1 覆盖。
2. 同源数据跨 split、合成标签冒充人工真值、非有限或完全静音音频：冻结/审计失败有明确原因，任务 1、2 覆盖。
3. 中断后读到旧 response、重复运行计费或重复成功结果：显式恢复、哈希绑定和不盲重试，任务 3、6 覆盖。
4. 超快喂完音频、partial 当 final、跨 clip 上下文残留：pacing、唯一 final 和新建 state，任务 5 覆盖。
5. 未回听即完成审阅、纠正覆盖历史、未完成运行被计分或 test 进入训练：状态与来源隔离，任务 4、7、8 覆盖。

## 任务 0 接手、迁移规划与原测试基线

**Files:** 建立已有仓库本地克隆；复制本设计与计划到同名 docs/superpowers 位置。新增 `experiments/duplexlab/README.md`；本地证据位于 `runs/duplexlab/bootstrap-<时间>/`。

**Interfaces:** 输入为已有远端；输出为确认的 checkout、源码 SHA、轻量开发环境与原测试报告。没有生产行为变更。

- [ ] 先确认目标路径不存在或核对已存在仓库的 remote、分支和未提交内容。需要隔离时按 using-git-worktrees 处理；不移动其他任务文件。
- [ ] 仅在路径确实不存在时执行：

```bash
git clone https://github.com/HenryVarro666/local-speaker-lab.git /path/to/projects/local-speaker-lab
cd /path/to/projects/local-speaker-lab
git status --short
git log -1 --format='%H %s'
git switch -c feat/duplexlab
```

- [ ] 检查 clone 中是否新增 AGENTS/CLAUDE 指令并遵守；确认 725 条任务的负责人和运行机器，本轮不启动/重启它。保存两份历史协议的 tracked 文件哈希及当前 diff。
- [ ] 迁入两份技术文档，之后只在新 checkout 更新本计划复选框；voice_ai 总路线指向该执行副本。
- [ ] 在仓库根目录建立轻量环境。当前以下工具版本取自已读仓库文件，执行时先核对是否已变：

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-dev
.venv-dev/bin/python -m pip install --upgrade --only-binary=:all: -r requirements/bootstrap.txt
.venv-dev/bin/python -m pip install --build-constraint requirements/bootstrap.txt -r requirements/dev.txt
.venv-dev/bin/python -m pip install --no-build-isolation --editable '.[dev]'
.venv-dev/bin/python -m pip check
.venv-dev/bin/python -m pytest -q -rs
.venv-dev/bin/python -m speaker_lab --help
.venv-dev/bin/python -m speaker_lab.worker --help
```

- [ ] 保存完整输出与退出码。通过数不预填；Mac 不支持的测试保留具体跳过/失败原因，先区分原失败再开发。基础层不安装 Gradio、Torch 或 vLLM。

**Exit:** 原仓库入口可用，基线结果已保存，已知任务不冲突。环境安装失败时先解决此门槛，不直接转 GPU 安装。没有 commit/push 步骤。

## 任务 1 manifest 与冻结协议

**Files:** Create `src/speaker_lab/duplex/{__init__.py,__main__.py,cli.py,protocol.py}`、`configs/duplexlab.example.toml`、`tests/test_duplexlab_protocol.py`；样例为自写 JSONL，不包含第三方音频。

**Interfaces:** `load_manifest(path: Path, data_root: Path) -> list[dict]`、`freeze_protocol(manifest: Path, data_root: Path, config: Path, output: Path) -> dict`、`verify_protocol(protocol_dir: Path, data_root: Path) -> list[dict]`；CLI `freeze --manifest --data-root --config --output`。

- [ ] 先写拒绝重复 ID、错误哈希、路径越界、符号链接越界、同源跨 split 的测试；另测目录位置变化不影响内容哈希，fixture 与 synthetic 身份不丢失。
- [ ] 运行 `.venv-dev/bin/python -m pytest tests/test_duplexlab_protocol.py -q`，确认缺少新模块时失败。
- [ ] 实现设计 §4 数据字段与配置；冻结到不存在的新目录，不覆盖旧协议。完整验证后一次发布 FREEZE.json；不将部分输出当冻结成功。
- [ ] 相同测试通过；`python -m speaker_lab.duplex --help` 与 `freeze --help` 不导入 Torch。使用合成生成的临时 WAV 验证正常冻结和篡改后的拒绝，不用真实模型。

**Exit:** 20 条开发 manifest 可冻结并复验；只有 schema 和哈希通过，不声称语音内容正确。

## 任务 2 音频审计与精确去重

**Files:** Create `duplex/audio.py`、`tests/test_duplexlab_audio.py`；Modify `duplex/cli.py`；输出到新 `runs/duplexlab/<run>/audit.jsonl`，规范 PCM 在本地 data/duplexlab/derived/。

**Interfaces:** `audit_clip(record: dict, data_root: Path, derived_root: Path, rules: dict) -> dict`、`find_exact_duplicates(records: list[dict]) -> list[dict]`；CLI `audit --protocol --data-root --output`，规则来自冻结 config。

- [ ] 测试损坏/零帧、NaN、完全静音、1 秒和 12 秒边界，以及有停顿但包含有效语音；原音哈希在操作前后相同。
- [ ] 测试两种无损封装解码到相同 PCM 可归为重复、幅度不同的音频不能被自动同一化；重复跨 split 必须报错而非静默丢掉 test。
- [ ] 测试先检查原音削波/静音特征，再生成规范 PCM；按设计初始阈值区分 pass、needs_review 与 reject。复用已有音频能力但不调用会提前拒绝静音的路径掩盖原因。
- [ ] 运行 `.venv-dev/bin/python -m pytest tests/test_duplexlab_audio.py -q` 完成失败→实现→通过；再用本人/有权使用的 20 条开发录音作真实审计，保留逐条原因。

**Exit:** 每条都有去向和原因；只实现文件与 PCM 精确去重，不写成近重复/说话人去重已完成。

## 任务 3 可恢复的离线 ASR 基线

**Files:** Create `duplex/store.py`、`duplex/runner.py`、`tests/test_duplexlab_store.py`、`tests/test_duplexlab_runner.py`；Modify `duplex/cli.py`；不改原 runner/worker 的公共协议。

**Interfaces:** `RunStore(db_path: Path)`，方法 `start_attempt(clip_id: str, condition: str) -> int`、`finish_attempt(clip_id: str, condition: str, attempt: int, result: dict) -> None`、`fail_attempt(..., error: str) -> None`、`iter_results() -> list[dict]`、`put_review(review: dict) -> None`；`run_offline(protocol_dir: Path, config: dict, output_dir: Path, resume: bool=False) -> dict`。省略号方法的完整参数与 finish_attempt 相同但以 error 替换 result。

- [ ] 测试成功任务不重复、失败显式恢复、配置改变拒绝恢复、旧进程仍在运行拒绝接手、遗留 running 不当成功、旧 response 不复用。SQL 唯一键与写结果/成功状态同事务。
- [ ] 用已有 fake backend 完成两条任务与一个故意失败任务，验证不完整 run 不能导出完整比较。测试中不启动模型。
- [ ] 新 loader 构造原 WorkerRunner 所需的 `_root`、`workers.transcribe_python`、timeout 和 `transcribe` 配置，调用其 transcribe 阶段。job 包含 id/audio_path/start/speaker；批量请求一次加载模型，完整检查返回 ID。
- [ ] 显式离线配置 `language=""`、`aligner=""`、`max_new_tokens=256`，使用 0.6B 模型的固定 revision；测试没有继承 Chinese 默认或隐式加载强制对齐模型。
- [ ] 新增 CLI `run --protocol --data-root --config --output [--resume]`；不经过原四阶段 config loader。
- [ ] 运行 `.venv-dev/bin/python -m pytest tests/test_duplexlab_store.py tests/test_duplexlab_runner.py -q`。随后在可用模型环境用 3 条非测试集录音真实 smoke，再完成 20 条开发基线。

**Exit:** 每条原始输出、模型版本、加载/推理时间和失败可查；在此阶段 mode 固定 offline，不报告实时延迟。

## 任务 4 计分、回听、纠正与第一版报告

**Files:** Create `duplex/metrics.py`、`duplex/review.py`、`duplex/report.py`、`tests/test_duplexlab_metrics.py`、`tests/test_duplexlab_review.py`、`tests/test_duplexlab_report.py`；Modify cli。

**Interfaces:** `score_run(run_dir: Path, protocol_dir: Path, data_root: Path) -> dict`、`build_review_packet(run_dir: Path, output_dir: Path) -> Path`、`import_reviews(run_dir: Path, review_file: Path) -> dict`、`render_report(run_dir: Path, output: Path, public: bool=False) -> Path`。

- [ ] 测试总体分数按编辑数和参考 token 聚合；中文、英文、mixed 分组独立；空参考与缺失预测单独报告；fixture 不进入质量表；不完整 run 拒绝正式计分。
- [ ] 新评分调用原 score_pair/aggregate_scores，另存 normalization_version，不改变历史 scorer。先用 3 对人工可算的例子验证，再计真实 20 条。
- [ ] 回放参考旧听音页，音频默认本地引用；标签和转写 HTML 转义。记录 listened/reviewer_id/answer_exposed，批准时校验当前音频/协议哈希。重复导入幂等，冲突保留两版本，不覆盖源 reference。
- [ ] 测试未听音不能标为完成人工、哈希改变拒绝导入、含 `<script>` 的预测只能作为文字显示、公开模式不泄漏绝对路径/第三方原文。
- [ ] CLI 提供 `score --run --protocol --data-root --output`、`review --run --output`、`import-reviews --run --file`、`report --run --output [--public]`。公开汇总仅统计与明确允许公开的示例。
- [ ] 运行三个新测试文件，并实际在浏览器回听至少 3 条；不能只看 HTML 源码。人工核对播放器、文字换行、修订记录和导出；生成页面不代替人工听音。

**Exit:** 可交付第一版离线 Demo：真实识别→错误回放→审阅→版本记录。若尚无用户/人工听音，页面状态保持 pending，不伪造审阅结果。

## 任务 5 原生流式适配与计时

**Files:** Create `duplex/streaming.py`、`tests/test_duplexlab_streaming.py`；Modify metrics/cli，配置加入 streaming 独立 Python 与模式。

**Interfaces:** `replay_stream(asr: object, samples: np.ndarray, settings: dict, clock: object, emit: Callable[[dict], None]) -> dict`；`run_streaming(protocol_dir: Path, config: dict, output_dir: Path) -> dict`；`score_stream_events(events: list[dict], speech_bounds: dict) -> dict`。clock 提供 `monotonic_ns()` 与 `sleep(seconds)`，真实与测试实现同接口。

- [ ] 测试每块等音频时轴到达才送入、partial 为空不记首次文本、finish 只执行一次、每 clip 新 state、取消后无旧 final、部分异常保留 events 但不记成功。
- [ ] 用假时钟和固定 partial 序列精确验证首次 partial、最后有声到 final、前缀修订数。分段方法与参数保存 speech_bounds.json；不能把文件尾静音也计为用户讲话。
- [ ] 对接已核对官方 API；初始 step=500ms、内部 chunk=2.0s、unfixed_chunk_num=2、unfixed_token_num=5。原示例未 pacing 的循环只作 API 参考。
- [ ] 模型进程常驻一批任务，stdout 日志与事件文件分离，事件绑定 attempt 与递增 seq。native streaming 只在独立 vLLM 环境验证；没有可用显存时不加载。
- [ ] 运行 `.venv-dev/bin/python -m pytest tests/test_duplexlab_streaming.py -q`，再在 Linux 以至少 6 条真人/授权开发录音测真实事件；核验新模型一次加载、clip 间状态清空、所有 final 完整。

**Exit:** 真实流式 smoke + 原始事件可复算。失败时保留离线 Demo，报告 stream_not_verified，不用离线结果充数，也不为抢工期改现有服务。

## 任务 6 可选表达数据与两日演示

**Files:** Create `duplex/synthesis.py`、`tests/test_duplexlab_synthesis.py`、`experiments/duplexlab/scripts.example.jsonl`；Modify cli/report。

**Interfaces:** `synthesize_scripts(scripts: Path, config: dict, output_dir: Path, dry_run: bool=True) -> dict`；CLI `synthesize --scripts --config --output [--execute]`。config 中 enabled=false 且 max_cost_usd=0 为默认。

- [ ] 先用本人录音或已存在且有使用权的音频完成同文本不同表达的 3 对样本，不等待 API。
- [ ] 可选适配已核对的 Drama 3 API；具体请求 schema、费用及密钥由实施当天官方文档与账户验证，不能照搬未核验字段。密钥只读环境变量，不输出请求 headers。
- [ ] 测试默认不发网络、缓存命中不再请求、预算不足前置拒绝、语音和脚本哈希记录、超时未知计费不自动重试；API 错误不伪造音频。
- [ ] 授权和预算可用时先合成 1 条，经人工确认实际说出的文字再扩到最多 20 脚本×3 表达；人工未回听的 style_verified=false。所有变体跟随 script_id 分组。
- [ ] 录制 90 秒展示：一个成功基线、一个停顿/改口失败、一个审阅与导出过程。用字幕明确真人/合成、离线/流式、历史/当前模型；不加入未经实现的训练前后改善。

**Exit:** 有声音与可追溯处理流程的展示。任务 6 是可选增强；无 API 不阻塞任务 7、8。

## 任务 7 冻结训练与独立测试数据

**Files:** Create `duplex/datasets.py`、`tests/test_duplexlab_datasets.py`、`experiments/duplexlab/protocols/curation-pilot-v1/`；Modify cli。

**Interfaces:** `select_training_arms(pool: list[dict], predictions: list[dict], reviews: list[dict], policy: dict) -> dict[str, list[dict]]`、`export_training(arms: dict, data_root: Path, output_dir: Path) -> dict`；CLI `export-train --protocol --selection --data-root --output`。

- [ ] 审计 train/dev/test 的来源和历史使用。目标 dev=40、test=200 条真人，旧 200/725 validation 不作新盲测；没有可验证分组时披露 speaker independence 未知。
- [ ] 从官方 train 冻结最多 2000 条候选的来源与选择规则，对候选做同一基座离线转写；不使用 test 误差构造选择规则。A1 随机与 A2 筛选各 500 条；不足则另立较小 pilot，保持两臂同量。
- [ ] A2 明确采用 ASR 参考一致性排序：先排除 reject 和未裁定 needs_review，按训练参考与基座预测的 MER 递增，再按 silence_fraction、clip_id 排序；不是通用最优 curation，也不把模型一致当真值。A1 从同一有效池固定 seed=20261020 抽样。
- [ ] 两臂语言×时长桶配额相同，数量相同、总时长差≤1%；language 配额默认 mixed 250、zh 125、en 125。时长桶为 [1,3)、[3,6)、[6,12] 秒，桶配额在开发池统计后、正式挑选前冻结；无法匹配时报告不可行，不隐式改配额。
- [ ] 测试跨 split 的源家族/PCM 重复拒绝、未裁定不导出、fixture/synthetic 不进真人首轮、审阅纠正优先但源 reference 保留、预算不匹配拒绝、固定输入与种子导出一致。
- [ ] 输出各 arm JSONL（audio/text）、selection.json、来源与内容哈希、counts.json；dev 单独导出，test 不写到训练目录。text 前缀固定 zh→`language Chinese<asr_text>`、en→`language English<asr_text>`、mixed→`language None<asr_text>`；测试这三种映射，不构造 Mixed 语言标签。audio 在训练机器解析为绝对路径，另保留可移植来源哈希。
- [ ] 运行 `.venv-dev/bin/python -m pytest tests/test_duplexlab_datasets.py -q`，独立复算样本数、时长和交集，人工抽查若干已纠正条目。

**Exit:** 形成可训练、可追溯、预算匹配的三臂协议。ASR 一致性筛选偏向当前基座易识别样本的局限预先记录，不等结果后才解释。

## 任务 8 SFT smoke、训练与 checkpoint 验证

**Files:** Create `scripts/duplexlab_train.py`、`tests/test_duplexlab_training.py`、固定训练 TOML；上游代码放 `.cache/upstream/Qwen3-ASR/`，模型在 checkpoints/duplexlab/，不纳入 Git。

**Interfaces:** `build_training_command(config: dict, export_dir: Path) -> list[str]`；包装脚本接受 `--config --export-dir --output --dry-run`，执行前核对导出哈希、dev 路径和输出新目录。

- [ ] 固定上游 commit 与脚本 SHA，依照官方格式准备离线依赖环境。复用其数据 collator、prefix loss 与可推理 checkpoint 回调；不在原离线或流式环境原地升级 Transformers。
- [ ] 测试误把 test 作为 eval_file 时拒绝、没有 dev 时拒绝、同一路径覆盖时拒绝、导出哈希变化时拒绝、dry-run 不启动训练。只传实际存在的 CLI 参数。
- [ ] 先使用 8 train/4 dev 独立 smoke。初始 batch=1、grad_acc=8、lr=2e-5、epochs=1、num_workers=0、persistent_workers=0、save_steps=1、save_total_limit=2；这些小数据不用于结果表。
- [ ] 检查 loss 有限、至少一个 optimizer step、checkpoint 和处理器文件齐全，再实际从 checkpoint 加载并转写一条 smoke 音频。保存 GPU 峰值、耗时、版本；只有训练退出 0 不算重载成功。
- [ ] 两臂正式参数固定为 0.6B、batch=1、grad_acc=8、lr=2e-5、epochs=1、num_workers=0、persistent_workers=0、save_steps=50、save_total_limit=2，显式传同一 dev。seed=42 在 Trainer 配置和记录中核对；当前上游没有 --seed CLI，不杜撰开关。
- [ ] OOM 或处理器导出失败就保存失败；若改为 LoRA、梯度检查点或更短音频，另立配置与适配任务，两臂一致，不只让某一臂采用有利配置。
- [ ] 两臂各自训练、保存和重载成功后，冻结模型 SHA 与最终选用 checkpoint 规则。首轮只用一个 seed，报告 pilot。

**Exit:** 两个真实、可重载的训练 checkpoint；未完成时保持 training_incomplete，不写提升或生产就绪。

## 任务 9 冻结测试、流式回归和结果包

**Files:** `experiments/duplexlab/reports/curation-pilot-v1/RESULTS.md`、`summary.json`、允许公开的统计图；更新 experiments/duplexlab/README、docs/ROADMAP、必要的顶层 README 与第三方说明。

**Interfaces:** 复用任务 3/4/5，对 A0/A1/A2 同一 test、同一解码参数运行；新增 `compare_runs(run_dirs: list[Path], protocol_dir: Path) -> dict` 在 metrics.py。

- [ ] 测试三臂 ID/参考/模型映射完整、缺项拒绝、总体 MER 用总计数计算；质量差值采用真实配对，group 信息缺失时不冒充说话人聚类。
- [ ] 三臂完整运行冻结真人 test。保存原始预测、编辑数、语言/表达切片及 1000 次 seed=20261020 区间；不重复改变 test 或按效果提前停跑。
- [ ] 以 6–20 条固定开发流式样本重载并比较新 checkpoint；资源足够时再完成 ≥100 条冻结延迟集。离线变好而流式退化需并列报告，不隐藏。
- [ ] 给出工程完成状态与研究结论两个独立字段。差值区间跨零写“未获得明确改善证据”；合成测试结果与真人结果分开。初次 partial 不称首声，clip bootstrap 不称 speaker-disjoint。
- [ ] 全量 CPU 测试、原 CLI 及冻结文件检查通过；不为凑全绿删除平台失败。人工查看公开报告和至少 3 个音频案例，核对图表确实来自本次 JSON。
- [ ] 保存每个产物的路径与哈希，写第二版 90 秒演示和一条复现入口；最后列出本地修改/模型运行/部署/提交/推送各自状态。提交和推送等待用户明确指令，不自动执行。

**Exit:** 数据→训练→评测有完整证据，无需正提升也能完成实验。之后再选一种扩展：合成数据训练、原生全双工、Avatar 或多种子复验。

## 执行状态与自查

初版规划时任务 0–9 全部未执行；后续执行已取代该快照。当前看[主仓库计划](https://github.com/HenryVarro666/local-speaker-lab/blob/main/docs/superpowers/plans/2026-10-20-duplexlab-implementation.md)，不要据本归档重新创建环境或重跑已完成模型任务。

设计覆盖：路径与冻结→任务 1；音频与去重→2；恢复与模型隔离→3；审阅/计分/导出隐私→4；原生流式与同钟计时→5；表达素材与预算→6；数据切分和对照→7；训练/重载→8；结果和原功能回归→9。沿用用户默认的直接执行方式，无子代理或自动 commit 步骤。

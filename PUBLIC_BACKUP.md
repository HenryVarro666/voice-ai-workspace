# 从原工作目录同步五个 GitHub 公开备份

继续在原来的四个代码目录开发；根目录仍不是 Git 仓库。`backup_public.py` 从原文件生成经过筛选的公开快照，再更新五个独立公开仓库。原目录的 Git 历史、暂存区和分支不参与推送。

## 日常操作

在 `voice_ai` 根目录执行（也可以用脚本的绝对路径，从其他目录执行）：

```sh
python3 backup_public.py preview
python3 backup_public.py show <计划ID> --diff
python3 backup_public.py push <计划ID>
```

`preview` 是默认动作，直接执行 `python3 backup_public.py` 也只会生成预览。它会联网读取五个远端最新分支，在 `.public-backup/plans/<计划ID>/` 创建隔离候选，显示逐仓库新增/修改/删除和行数统计。`show --diff` 展示完整内容差异；`changes.md` 和各仓库 `.diff` 保存在计划目录。先检查所有删除、README/实验数字和新增数据文件。

`push` 再展示清单，要求手动输入 `PUSH <计划ID>`。没有免确认选项。确认后仅推送这个已审核候选；所有仓库都无改动时不产生新的提交。预览后选中的源文件、脚本、配置、误报例外表或远端变化，推送会停止，需要重新 `preview`。被排除的模型或录音变化不影响源码计划。

本机已执行一次 `init` 建立与 2026-10-22 首次发布的对应基线，不要在每次备份前重新初始化。Python 3.11+、Git、Gitleaks 必须可用，GitHub HTTPS 推送需本机已有 Git 凭据。本工具不会保存 token；没有 Gitleaks 就停止。

## 五个去向

路径相对于本工作目录。精确配置见 `public_backup_config.json`。

| 原目录 | GitHub 仓库 | 分支 |
|---|---|---|
| `dsh-voice-ai-girlfriend/` | [dsh-voice-ai-girlfriend](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend) | `main` |
| `dsh-voice-ai-girlfriend-plugin/` | [dsh-voice-ai-girlfriend-plugin](https://github.com/HenryVarro666/dsh-voice-ai-girlfriend-plugin) | `master` |
| `../local-speaker-lab/` | [local-speaker-lab](https://github.com/HenryVarro666/local-speaker-lab) | `main` |
| `../speech-avatar/` | [speech-avatar](https://github.com/HenryVarro666/speech-avatar) | `main` |
| `./` 中选定的文档和备份工具 | [voice-ai-workspace](https://github.com/HenryVarro666/voice-ai-workspace) | `main` |

公开 checkout 仍在 `../voice-ai-publication-2026-10-22/exports/` 下，成功推送后由脚本快进到已验证的远端提交。不要把 DSH 原工作区的 `origin` 改成公开备份然后直接推送：原历史含视频。插件已有正式 fork，无需再次 fork。

## 保留的排除与审核规则

采用“目录/文件允许清单＋硬排除＋内容扫描”。`include` 指定哪些位置允许自动发现新文件；已经公开且仍在原目录中的文件继续跟踪修改与删除。远端独有文件保留。新顶层模块或新的实验报告目录需要显式加进 `include`，然后重新预览。

- 排除 `.env*`、常见凭据文件、私钥、实际 `bridge-config.json`、`.local.` 配置、虚拟环境、缓存、模型/检查点、构建物、日志和运行输出。
- 排除模型权重、归档、数据库和音视频，包括 `.wav.txt` 这类复合后缀。文本里嵌入的 base64 媒体也会阻止发布。
- 默认仅允许源码/文档/结构化文本。13 个已审核图表 PNG 是精确路径例外；新图片需明确审核后添加到 `approved_binary_paths`，不能凭目录通配放行。
- 本地符号链接、Git 子模块、未审核二进制和大于 25 MiB 的源文件不会发布。凭据候选由内置规则与 Gitleaks 双重检查，扫描失败时停止。
- `public_backup_allowlist.json` 仅保留首次发布已审核的非秘密误报：实验编号、SHA256、浏览器偏好键和合成测试 token。例外绑定仓库、路径、规则和完整行的 SHA256；不按整文件忽略。新发现记录位置与指纹，不显示凭据值。若发现真实凭据，先从源文件移除并按需撤销；不要加入例外表。

允许公开的 JSON/CSV 不等于它们自动没有个人信息。预览需要人工检查新增元数据；扫描不能代替对数据内容的判断。

## 公开进度与实验怎么维护

根目录的 `PROJECT_STATUS.md`、`EVOLUTION.md`、`DUPLEXLAB_ROADMAP.md` 保留本地完整协作记录。对应 GitHub 页面分别来自 `public_docs/` 中同名的公开摘要；更新时只把适合公开的结论写到这里。`public_docs/` 本身不会作为额外目录上传，脚本将三份文件映射到文档仓库根目录。Speech Avatar 也从它自己的 `public_docs/PROJECT_STATUS.md` 与 `public_docs/EVOLUTION.md` 发布两份已审查摘要，避免把并行实验的实时日志带入备份。其他 README、实验索引和代码继续从原路径读取。

README 英文/中文同步写产品场景、方法、已证实结果、局限与下一项决定；实验目录保留冻结协议、失败与采用结论。Local Speaker Lab 和 Speech Avatar 的新实验目录默认不自动全量发现：审核计划、汇总指标和图后，逐文件或指定安全子目录加入 `include`。不要把整个实验工作目录加入清单。已有公开实验文件的后续修改会自动进入预览。

脚本保留已整理的公开文档差异，只把源目录相对上次成功备份的变化合入当前远端。非重叠修改可三方合并；同一处冲突、远端删除冲突或新文件同名冲突会停止。它会改写已选 Markdown 的本地/跨仓库链接，标记没有发布的本地材料，并沿用首次发布的路径/姓名脱敏规则；最终内容以预览 diff 为准。

每轮候选重建 `PUBLICATION_MANIFEST.json` 的文件哈希，文档总仓库的 `REPOSITORIES.json` 固定本轮四个代码候选的提交。`PUBLICATION_AUDIT.json` 保留首次发布审计快照；后续扫描与推送回执在本地计划目录，不把旧测试结果说成本轮测试。

## 失败、恢复与换目录

- **本地源变化或远端先更新：** 重新 `preview`、查看新 diff，再推送新计划。检查在任何仓库开始推送前完成；推送也不用 force。
- **某仓库推送中断：** 五个 GitHub 仓库没有共同事务。已成功仓库记录在 `push-receipts.json`；环境和源文件未变时，可再次 `push` 同一个计划，已成功仓库不会重复提交。若又修改了源文件，改用新预览。
- **公开 checkout 有未提交内容：** 先人工处理，脚本不会 reset/clean。GitHub 新历史若引入凭据、媒体/权重，或重写已审核历史，停止并人工处理。
- **换电脑/移动目录：** 先克隆五个公开仓库，调整配置中的 `source`、`public_checkout`。恢复原工作目录后，若没有 `public_docs/`，从公开文档仓库的三个同名根目录页面复制到该目录。复制 `.public-backup/state.json` 及 `objects/` 可保留三方同步基线；`plans/` 可丢弃。没有旧状态时执行一次 `init`；无法与旧发布对应的差异仍留给第一次预览，不会静默覆盖。迁移后重新预览，不复用旧机器的计划。
- **回收空间：** 完成后可人工删除不需要的旧 `plans/<ID>/`；保留 `state.json`、`objects/`，需要追溯时另存推送回执。不要删除原始媒体或模型来“清理备份”。

回归演练仅使用临时目录和本地 bare Git remotes，不访问真实 GitHub，也不运行语音/GPU服务：

```sh
python3 -m unittest discover -s tests -p test_public_backup.py -v
```

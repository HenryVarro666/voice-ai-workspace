# Maintaining the five public backups

Each repository owns its README and experiment index. Update both overview languages when a feature, command, number or adoption decision changes. Keep the chronological evidence and failure records; summarize decisions at the top level.

The DSH bridge publication is a source-only snapshot because its original upstream history contains video. Future updates must be reviewed source diffs against this clean checkout; pushing the original media-bearing history would violate this backup's scope.

The browser plugin retains its upstream fork history. Local Speaker Lab retains its existing public history and includes the latest remote documentation changes. Speech Avatar and this documentation hub have initial source/document histories.

For an update, keep working in the original source directories and run `python3 backup_public.py preview`. Inspect the per-repository change list and `show <plan-id> --diff`; run relevant project tests before `push <plan-id>`. Push repeats the list and requires typing `PUSH <plan-id>`. The helper scans credentials, preserves exclusions and curated public changes, refreshes file manifests and pins code commits in REPOSITORIES.json. See [the repeatable backup guide](PUBLIC_BACKUP.md) for setup, selection rules, conflicts and partial-push recovery. PUBLICATION_AUDIT.json remains the initial publication audit; later scan reports and exact push receipts are local to each plan.

The documentation hub maps its three coordination pages from `public_docs/` in the original workspace. Speech Avatar maps its status and evolution pages from its own `public_docs/` directory, so ongoing experiment logs can change independently. Keep full private coordination logs separate and update those public summaries deliberately. Existing experiment evidence remains tracked, while new experiment directories require an explicit selection in public_backup_config.json.

Raw media, weights and private operational records are deliberately not backed up here. A GitHub source backup is not an archival copy of those excluded artifacts. Publishing code does not modify the running services.

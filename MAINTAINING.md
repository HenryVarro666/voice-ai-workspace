# Maintaining the five public backups

Each repository owns its README and experiment index. Update both overview languages when a feature, command, number or adoption decision changes. Keep the chronological evidence and failure records; summarize decisions at the top level.

The DSH bridge publication is a source-only snapshot because its original upstream history contains video. Future updates must be reviewed source diffs against this clean checkout; pushing the original media-bearing history would violate this backup's scope.

The browser plugin retains its upstream fork history. Local Speaker Lab retains its existing public history and includes the latest remote documentation changes. Speech Avatar and this documentation hub have initial source/document histories.

For an update: inspect the source diff, select code and approved metadata, preserve licenses, run relevant tests, verify local/cross-repository links, scan credentials and inspect the staged file list. Refresh PUBLICATION_MANIFEST.json and PUBLICATION_AUDIT.json to describe what was actually checked. Then commit and push the reviewed public checkout.

Raw media, weights and private operational records are deliberately not backed up here. A GitHub source backup is not an archival copy of those excluded artifacts. Publishing code does not modify the running services.

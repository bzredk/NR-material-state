# Local workcopy snapshot

This preserves the pre-existing `reproductions/history-dependence`, `e2`, `e3` and `lab` working copies during the 2026-10-26 cleanup. It is an archive operation, not a new experiment.

All 738 non-cache files were reconstructed and checked byte for byte against the original working copies before removal. The original history-dependence, controller-transfer and shared-feedback data, negative results and checkpoints remain in `1D/`. Files already present there are referenced by path and SHA256 in `manifest.json`. The 36 unique payloads are stored in `overrides.zip`, including local notes, modified reports, figure exports and interface-validation records.

Restore one complete workcopy from the project root:

```sh
python 1D/tools/restore_workcopy.py --archive 1D/provenance/workcopies/20261026_cleanup --experiment controller-transfer --destination reproductions/controller-transfer
```

Choose `history-dependence`, `controller-transfer`, `shared-feedback` or `material-collection`. The destination must not exist. Restoration checks each payload once before writing and keeps the destination inside this project. Caches are regenerated normally. Keep this archive together with the referenced `1D/` files.

`restore_verification.json` records the successful full restoration check. `cleanup.json` records removed paths and reclaimed space. The remaining `reproductions/cpu-replay.jsonl` and `cuda-replay.jsonl` are unique logs and remain in place. No 2D solver data, physical failures, Windows environment or running editor state was removed.

After cleanup, all 1,149 protected file hashes were unchanged. The Linux container's four contract tests passed in 1.38 s, and the CLI reopened the verified 2D pilot. See `preservation_check.json` and `checks.json`.

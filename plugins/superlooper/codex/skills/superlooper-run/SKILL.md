---
name: superlooper-run
summary: Prepare and execute the Superlooper run stage through the Codex dispatcher.
description: Prepare and execute the Superlooper run stage through the Codex dispatcher.
---

# Superlooper Run

Explicit invocation: `$superlooper-run <session_id>`.

For every shared script, resolve `plugin_root` from the directory of this loaded `SKILL.md` as `../../..`; never resolve `scripts/...` relative to the target workspace. Invoke `<plugin_root>/scripts/<script>.py` with `--workspace-root .`.

Use the approved `.superlooper/` session state and module split to generate the shared execution manifest with `scripts/generate_execution_manifest.py --platform codex`. Generate the execution summary with `scripts/build_execution_summary.py` and stop for the existing execution-summary approval.

After approval, read only the relevant node payload from the execution manifest and apply the Codex dispatcher contract in `codex/dispatcher/README.md`. Preserve the chain `mod_* -> task_code_review -> task_merge -> task_integration_test -> task_apply_to_workspace`; use the existing review, merge, test, apply, and requirement-verifier report gates. Do not bypass the shared `.superlooper/` state or quality gates.

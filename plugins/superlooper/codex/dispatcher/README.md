# Codex Dispatcher Contract

## Scope

This directory defines the Codex-only adapter from the shared execution Manifest to Codex native multi-agent calls. It does not replace the shared session state, reports, validators, merge logic, test logic, or apply logic stored under `.superlooper/`.

## DAG

```text
mod_* -> task_code_review -> task_merge -> task_integration_test -> task_apply_to_workspace
```

## Node contract

| Node | Codex input | Required output |
| --- | --- | --- |
| `mod_*` | Current node payload, design directory, and current module object | Current module output directory and `artifact_manifest.json` |
| `task_code_review` | All module outputs | `code_review_report.md` |
| `task_merge` | Reviewed artifact manifests | `merge_report.json` |
| `task_integration_test` | Merged tree and design/Manifest traceability | `test_report.md` |
| `task_apply_to_workspace` | Merge report and merged tree | `apply_report.json` or an apply conflict report |

## Native dispatch rules

- The parent Codex session calls the native `spawn_agent` tool directly for eligible `mod_*` nodes, using the Task 1 verified `task_name`, `fork_turns`, and `message` parameters.
- Each child receives only its current node payload, its module object, and the explicitly listed design context. It must not receive the original requirement document, another module payload, or another module output directory.
- A parent session that needs `spawn_agent` uses a non-ephemeral, read-only Codex session. The parent waits for child results and writes only the shared `.superlooper/` contract outputs.
- Quality nodes run only after their declared dependencies have succeeded. Existing validators and reports remain authoritative for every gate.
- The adapter never writes Claude-specific agent registration files.

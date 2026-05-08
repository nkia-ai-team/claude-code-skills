# Phase Contract — single source of truth

testbed-build 는 숫자 phase 대신 아래 `phase_id` 를 기준으로 실행, manifest,
resume, report 를 판단한다. 숫자는 사용자 안내용 표시일 뿐이며 다른 reference 에서
분기 기준으로 사용하지 않는다.

## Canonical phase order

| Order | phase_id | Required | Owner | Main artifact |
|---:|---|---|---|---|
| 0 | `bootstrap` | yes | orchestrator | `bootstrap.yaml` |
| 1 | `interview` | yes | orchestrator | `interview.yaml` |
| 2 | `precheck` | yes | orchestrator | manifest only |
| 3 | `architecture` | yes | orchestrator | `architecture.md` |
| 4 | `user_approval` | yes | orchestrator | manifest only |
| 5 | `existing_testbed_detect` | conditional | orchestrator | manifest only |
| 6 | `lock_acquired` | yes | orchestrator | `.locks/<target>_<cluster>.lock` |
| 7 | `services_author` | conditional | `testbed-engineer` | verdict outputs |
| 8 | `inventory_generated` | yes | orchestrator | `inventory.yml` |
| 9 | `ansible_deploy` | yes | `testbed-deployer` | `deploy.log`, verdict |
| 10 | `sanity_check` | yes | orchestrator | manifest only |
| 11 | `polestar10_register` | yes | `testbed-polestar10-register` | `register.json` |
| 12 | `generate_scenarios` | yes | `testbed-generate-scenarios` | `scenarios.json` |
| 13 | `tune_alarms` | yes | `testbed-tune-alarms` | `alarms.json` |
| 14 | `verify` | yes | `testbed-verifier` | `verify.log` |
| 15 | `finalize` | yes | orchestrator | report markdown |
| 16 | `cleanup` | conditional | orchestrator | manifest only |

## Allowed phase states

```yaml
pending: not started
in_progress: started but not completed
completed: completed successfully
completed_with_warnings: completed, but report must mention warnings
skipped: intentionally skipped because its condition was false
failed: failed and should be resumable from this phase
finalized_partial: final report written even though verify did not PASS
```

Rules:
- Conditional phases must be written as `skipped`, not left `pending`.
- A failed required phase must not be silently advanced to the next phase.
- `finalized_partial` is valid only for `finalize` when verify max attempts ended
  in PARTIAL/FAIL and the user chose to write a report anyway.
- Cleanup is never used as a proxy for success. It records resource cleanup only.

## Dispatch contract

Every sub-agent or sub-skill dispatch returns or writes one standard verdict envelope:

```json
{
  "phase": "ansible_deploy",
  "verdict": "ok|warn|fail|skipped",
  "summary": "80 chars or less",
  "outputs": {},
  "errors": [],
  "next_action": "proceed|warn|retry|user-decision|dispatch_tune_and_retry"
}
```

The `phase` field must use `phase_id`, not display names such as numeric phases or
legacy names such as `ansible-deploy`.

## Manifest update contract

At the start and end of every phase:

```yaml
current_phase: ansible_deploy
phases:
  ansible_deploy:
    status: in_progress
    started_at: 2026-05-08T10:00:00Z
    completed_at: null
    attempts: 1
    verdict_path: null
    artifact_paths:
      deploy_log: deploy.log
```

On completion, update `status`, `completed_at`, `last_verdict`, and
`artifact_paths`. Use atomic writes (`manifest.yaml.tmp` then `mv`).

## Resume contract

Resume starts at the first required phase whose status is not `completed`,
`completed_with_warnings`, or `skipped`. For `verify`, resume continues from the
next attempt recorded in `verify_attempts`.

If the manifest is missing a phase key from this contract, migrate it in memory
by inserting the missing phase with `pending`, then persist the migrated manifest
before continuing.

# State Schema — `~/.testbed-build/`

testbed-build 의 모든 상태가 살아있는 디렉토리. phase id, 순서, 상태 enum 은
[phase-contract.md](phase-contract.md) 를 따른다.

## 디렉토리 레이아웃

```
~/.testbed-build/                                  chmod 700
├── bootstrap.yaml                                 chmod 600 — 자격증명 + 레포 경로 (영구)
├── reports/                                       영구 보존
│   ├── 2026-04-30-153022-plopvape-shop-v2.md
│   └── 2026-05-02-094500-core-banking.md
├── learnings.md                                   반복 이슈 누적 (Phase later)
├── .locks/                                        runtime 만 존재
│   └── 203.0.113.109.lock                      flock target
├── archive/                                       (선택) zip 백업
│   └── 2026-04-30-153022.zip
└── runs/                                          진행 중 + 실패 케이스만 잔존
    └── 2026-04-30-153022/                         RUN_ID = $(date +%Y%m%d-%H%M%S)
        ├── manifest.yaml                           phase-checkpoint
        ├── interview.yaml                          interview 결과
        ├── architecture.md                          architecture 산출 (scenarios/alarms 후 재작성)
        ├── inventory.yml                           inventory_generated 산출 (ansible 입력)
        ├── deploy.log                              ansible_deploy stdout/stderr
        ├── register.json                           polestar10_register 산출 (자원 ID 매핑)
        ├── scenarios.json                          generate_scenarios 산출
        ├── alarms.json                             tune_alarms 산출
        ├── verify.log                              verify attempt 누적
        └── metrics-snapshot.json                   testbed-tune-alarms 가 캐시
```

## 각 파일이 다음 phase 의 입력으로

| 파일 | 작성 phase | 읽는 phase | 누가 |
|---|---|---|---|
| bootstrap.yaml | `bootstrap` | 모든 phase | testbed-build 자체 |
| interview.yaml | `interview` | `architecture`, `inventory_generated`, `ansible_deploy`, `tune_alarms`, `verify` | testbed-build 자체 |
| architecture.md | `architecture` | `user_approval`, `finalize` | testbed-build 자체 |
| inventory.yml | `inventory_generated` | `ansible_deploy` | ansible-playbook |
| deploy.log | `ansible_deploy` | `ansible_deploy` 실패 진단, `finalize` | testbed-deployer agent |
| register.json | `polestar10_register` | `generate_scenarios`, `tune_alarms`, `verify`, `finalize` | testbed-polestar10-register |
| scenarios.json | `generate_scenarios` | `verify`, `finalize` | testbed-generate-scenarios |
| alarms.json | `tune_alarms` | `verify`, `finalize` | testbed-tune-alarms |
| verify.log | `verify` | `finalize` | testbed-verifier agent (append per attempt) |

## manifest.yaml — 단일 source of truth

phase 진행 추적. 매 phase 완료 후 즉시 갱신. resume 시 read.

```yaml
run_id: 2026-04-30-153022
testbed_name: plopvape-shop
target_host: 203.0.113.109
mode: 1
created_at: 2026-04-30T15:30:22Z
last_updated_at: 2026-04-30T15:32:08Z

manifest_version: 2
current_phase: ansible_deploy

phases:
  bootstrap:
    status: completed       # pending | in_progress | completed | completed_with_warnings | skipped | failed | finalized_partial
    attempts: 1
  interview:
    status: completed
    attempts: 1
  precheck:
    status: completed
    attempts: 1
  architecture:
    status: completed
    attempts: 1
  user_approval:
    status: completed
    attempts: 1
  existing_testbed_detect:
    status: skipped
    attempts: 0
  lock_acquired:
    status: completed
    attempts: 1
  services_author:
    status: skipped
    attempts: 0
  inventory_generated:
    status: completed
    attempts: 1
  ansible_deploy:
    status: in_progress
    attempts: 1
    artifact_paths:
      deploy_log: deploy.log
  sanity_check:
    status: pending
    attempts: 0
  polestar10_register:
    status: pending
    attempts: 0
  generate_scenarios:
    status: pending
    attempts: 0
  tune_alarms:
    status: pending
    attempts: 0
  verify:
    status: pending
    attempts: 0
  finalize:
    status: pending
    attempts: 0
  cleanup:
    status: pending
    attempts: 0

verify_attempts: []          # phase=verify 진행 시 attempt 누적: [{n: 1, verdict: PARTIAL, missed: [...]}, ...]
last_error: null              # 실패 phase 의 err 메시지 (resume 안내용)

artifacts:                    # 산출 파일 inventory (relative paths)
  interview: interview.yaml
  architecture: architecture.md
  inventory: inventory.yml
  deploy_log: deploy.log
  register: register.json
  # ...
```

## register.json 스키마

testbed-polestar10-register 가 `polestar10_register` 에 작성:

```json
{
  "run_id": "2026-04-30-153022",
  "registered_at": "2026-04-30T15:50:00Z",
  "polestar10_base": "https://198.51.100.96",
  "sms_host": {
    "agent_id": "MA_109_20260430153950",
    "host": "203.0.113.109",
    "status": "UP"
  },
  "kcm_cluster": {
    "cluster_id": "cluster-abc123def",
    "namespace": "kube-system",
    "status": "UP"
  },
  "apm_services": [
    {"service_name": "order-service", "agent_id": "...", "resource_id": "..."},
    {"service_name": "product-service", "agent_id": "...", "resource_id": "..."}
    // ...
  ],
  "wpm_services": [
    {"service_name": "order-service", "agent_id": "...", "resource_id": "..."}
    // ...
  ],
  "dpm_resources": [
    {"name": "postgres@rca-testbed-v2", "resource_id": "...", "status": "UP"}
  ],
  "nms_devices": []           // interview.nms.enabled=false 면 빈 배열
}
```

## scenarios.json 스키마

testbed-generate-scenarios 가 `generate_scenarios` 에 작성:

```json
{
  "run_id": "...",
  "testbed_name": "plopvape-shop",
  "scenarios_added": [
    {
      "id": "scenario-01",
      "file_path": "<scenario_runner>/scenarios/services/plopvape-shop/scripts/scenario-01-inventory-lock.sh",
      "expected_alarms": ["DPM lock wait", "..."],
      "estimated_duration_sec": 360
    }
    // ...
  ],
  "yaml_path": "<scenario_runner>/scenarios/services/plopvape-shop/service-spec.yaml",
  "git_branch": "feat/scenarios-2026-04-30",
  "pr_url": "https://github.com/.../pull/42"
}
```

## alarms.json 스키마

testbed-tune-alarms 가 `tune_alarms` 에 작성:

```json
{
  "run_id": "...",
  "registered_at": "...",
  "policies": [
    {"name": "RCA-Testbed APM 임계치", "domain": "apm", "tag_value": "...", "policy_id": "..."}
  ],
  "individual_alarms": [
    {
      "resource": "order-service",
      "measurement": "apm.response_time_avg",
      "levels": {"l1": 1000, "l2": 2000, "l3": 3000, "l4": 5000},
      "alarm_id": "..."
    }
    // ...
  ]
}
```

## verify.log 스키마

testbed-verifier 가 `verify` attempt 마다 append:

```
=== attempt 1 (2026-04-30T16:10:00Z) ===
overall: PARTIAL
scenarios:
  - 01: PASS (3/3 fired)
  - 02: PARTIAL (4/5 fired, missed: ["DPM Lock 수 급증 (≥40 Lock)"])
  - 03: PASS
  - 04: FAIL (1/4 fired, missed: [...])
recommendations:
  - "scenario-02 의 'DPM Lock 수 급증' 미발화. LEVEL3 = 40 → 25 권고"
  - "scenario-04 의 다수 미발화. 부하 강화 또는 임계치 보수적 조정"

=== retune (2026-04-30T16:18:00Z) ===
testbed-tune-alarms 재호출: scenario-02, scenario-04 의 missed 메트릭 임계치 조정
변경:
  - DPM Lock 수: LEVEL3 40 → 25
  - APM 응답시간 (order/payment): LEVEL3 5000 → 3000

=== attempt 2 (2026-04-30T16:25:00Z) ===
overall: PASS
all 4 scenarios PASS
```

## 정리 룰

testbed-build `finalize` / `cleanup`:

| 종료 상태 | 처리 |
|---|---|
| 모든 required phase=completed | 1) report.md → reports/<RUN_ID>-<name>.md<br>2) (선택) zip → archive/<RUN_ID>.zip<br>3) runs/<RUN_ID>/ 삭제<br>4) lock release |
| verify PARTIAL/FAIL 후 사용자 finalize 선택 | finalize.status=`finalized_partial`, runs/<RUN_ID>/ 보존 권장, report 에 미통과 명시 |
| 일부 phase=failed | runs/<RUN_ID>/ 보존. lock release. 사용자 안내. |
| 일부 phase=in_progress (cancel) | runs/<RUN_ID>/ 보존. lock release. resume 가능 표시. |

## 마이그레이션 가이드

manifest.yaml 스키마가 변경되면 `manifest_version` 을 올린다. 현재 canonical schema 는 V2.
V1 manifest 를 resume 할 때는 [phase-contract.md](phase-contract.md) 의 누락 phase 를
`pending` 으로 삽입한 뒤 저장한다.

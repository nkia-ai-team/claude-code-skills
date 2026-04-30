# State Schema — `~/.testbed-build/`

testbed-build 의 모든 상태가 살아있는 디렉토리.

## 디렉토리 레이아웃

```
~/.testbed-build/                                  chmod 700
├── bootstrap.yaml                                 chmod 600 — 자격증명 + 레포 경로 (영구)
├── reports/                                       영구 보존
│   ├── 2026-04-30-153022-plopvape-shop-v2.md
│   └── 2026-05-02-094500-core-banking.md
├── learnings.md                                   반복 이슈 누적 (Phase later)
├── .locks/                                        runtime 만 존재
│   └── 192.168.200.109.lock                      flock target
├── archive/                                       (선택) zip 백업
│   └── 2026-04-30-153022.zip
└── runs/                                          진행 중 + 실패 케이스만 잔존
    └── 2026-04-30-153022/                         RUN_ID = $(date +%Y%m%d-%H%M%S)
        ├── manifest.yaml                           phase-checkpoint
        ├── interview.yaml                          Phase 1 결과
        ├── architecture.md                          Phase 3 산출 (Phase 9, 10 재작성)
        ├── inventory.yml                           Phase 6 산출 (ansible 입력)
        ├── deploy.log                              Phase 7 stdout/stderr (testbed-engineer 진단 입력)
        ├── register.json                           Phase 8 산출 (자원 ID 매핑)
        ├── scenarios.json                          Phase 9 산출 (생성 파일 목록)
        ├── alarms.json                             Phase 10 산출 (등록 정책 목록)
        ├── verify.log                              Phase 11 attempt 누적
        └── metrics-snapshot.json                   testbed-tune-alarms 가 캐시
```

## 각 파일이 다음 phase 의 입력으로

| 파일 | 작성 phase | 읽는 phase | 누가 |
|---|---|---|---|
| bootstrap.yaml | 첫 호출 인터뷰 | 모든 phase | testbed-build 자체 |
| interview.yaml | 1 | 3, 6, 7, 8, 11, 12 | testbed-build 자체 |
| architecture.md | 3 | 4 (사용자 승인), 12 (보고서) | testbed-build 자체 |
| inventory.yml | 6 | 7 | ansible-playbook |
| deploy.log | 7 | 7 (실패 시) | testbed-engineer agent |
| register.json | 8 | 9, 10, 11 | testbed-polestar10-register |
| scenarios.json | 9 | 11, 12 | testbed-generate-scenarios |
| alarms.json | 10 | 11, 12 | testbed-tune-alarms |
| verify.log | 11 | 12 | testbed-verifier agent (append per attempt) |

## manifest.yaml — 단일 source of truth

phase 진행 추적. 매 phase 완료 후 즉시 갱신. resume 시 read.

```yaml
run_id: 2026-04-30-153022
testbed_name: plopvape-shop
target_host: 192.168.200.109
mode: 1
created_at: 2026-04-30T15:30:22Z
last_updated_at: 2026-04-30T15:32:08Z

phases:
  bootstrap: completed       # pending | in_progress | completed | failed
  interview: completed
  precheck: completed
  architecture: completed
  user_approval: completed
  lock_acquired: completed
  inventory_generated: completed
  ansible_deploy: in_progress
  polestar10_register: pending
  generate_scenarios: pending
  tune_alarms: pending
  verify: pending
  finalize: pending

verify_attempts: []          # phase=verify 진행 시 attempt 누적: [{n: 1, verdict: PARTIAL, missed: [...]}, ...]
last_error: null              # 실패 phase 의 err 메시지 (resume 안내용)

artifacts:                    # 산출 파일 inventory (relative paths)
  interview: interview.yaml
  architecture: architecture.md
  inventory: inventory.yml
  deploy_log: deploy.log
  register: register.json     # phase 8 후
  # ...
```

## register.json 스키마

testbed-polestar10-register 가 phase 8 에 작성:

```json
{
  "run_id": "2026-04-30-153022",
  "registered_at": "2026-04-30T15:50:00Z",
  "polestar10_base": "https://192.168.230.96",
  "sms_host": {
    "agent_id": "MA_109_20260430153950",
    "host": "192.168.200.109",
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

testbed-generate-scenarios 가 phase 9 에 작성:

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

testbed-tune-alarms 가 phase 10 에 작성:

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

testbed-verifier 가 phase 11 attempt 마다 append:

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

testbed-build phase 13 (cleanup):

| 종료 상태 | 처리 |
|---|---|
| 모든 phase=completed | 1) report.md → reports/<RUN_ID>-<name>.md<br>2) (선택) zip → archive/<RUN_ID>.zip<br>3) runs/<RUN_ID>/ 삭제<br>4) lock release |
| 일부 phase=failed | runs/<RUN_ID>/ 보존. lock release. 사용자 안내. |
| 일부 phase=in_progress (cancel) | runs/<RUN_ID>/ 보존. lock release. resume 가능 표시. |

## 마이그레이션 가이드

manifest.yaml 스키마가 변경되면 `manifest_version` 필드 도입 권장 (현재는 V1 가정 — 단일 세션 구현이라 마이그레이션 안 함).

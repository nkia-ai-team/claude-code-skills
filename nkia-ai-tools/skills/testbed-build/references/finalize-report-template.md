# Finalize Report Template

testbed-build Phase 12 인라인으로 채워 `~/.testbed-build/reports/<RUN_ID>-<TESTBED_NAME>.md` 에 저장.

## 변수 substitution

manifest.yaml + register.json + scenarios.json + alarms.json + verify.log 모두 source.

## 템플릿

```markdown
# RCA 테스트베드 구축 보고서

**Run ID**: {{RUN_ID}}
**Testbed**: {{TESTBED_NAME}}
**Target**: {{TARGET_HOST}} ({{TARGET_ARCH}})
**시작**: {{STARTED_AT}}
**완료**: {{FINISHED_AT}}
**소요**: {{DURATION_MIN}} 분
**최종 verdict**: {{FINAL_VERDICT}}   <!-- PASS / PARTIAL / FAIL -->

---

## 요약

{{ONE_LINE_SUMMARY}}

<!-- 예시: "plopvape-shop-v2 테스트베드를 203.0.113.109 에 구축. 6종 자원 등록 + 4 시나리오 + 12 알람 정책. closed-loop verify PASS (attempt 1)." -->

---

## 1. Architecture (인터뷰 답 + 산출 토폴로지)

{{ARCHITECTURE_SECTION}}    <!-- runs/<RUN_ID>/architecture.md 의 본문 -->

---

## 2. 서비스 배포 결과 (Phase 7)

| 항목 | 결과 |
|---|---|
| Ansible 실행 시간 | {{ANSIBLE_DURATION_MIN}} 분 |
| changed tasks | {{CHANGED_TASKS}} |
| K3s 버전 | {{K3S_VERSION}} |
| 배포된 서비스 수 | {{SERVICE_COUNT}} |
| DB 종류 | {{DB_KIND}} |
| Pod 상태 | {{POD_STATUS_SUMMARY}} |

상세 로그: `runs/{{RUN_ID}}/deploy.log` (또는 archive)

---

## 3. Polestar10 자원 등록 (Phase 8)

{{REGISTER_TABLE}}

<!-- 예시:
| 에이전트 | 등록 자원 | 상태 |
|---|---|---|
| SMS | 203.0.113.109 (호스트) | UP |
| KCM | cluster-abc123 | UP |
| APM | {{SERVICE_COUNT}} services ({{SERVICE_NAMES_INLINE}}) | UP |
| WPM | {{SERVICE_COUNT}} services (동일) | UP |
| DPM | postgres@rca-testbed-v2 | UP |
| NMS | (skip — interview.nms.enabled=false) | — |
-->

---

## 4. 시나리오 (Phase 9)

{{SCENARIOS_TABLE}}

<!--
| ID | 이름 | duration | expected_alarms |
|---|---|---|---|
| 01 | Inventory Row Lock | 360s | 3종 |
| 02 | External PG API Timeout | 300s | 5종 |
| 03 | PostgreSQL CPU Throttle | 300s | 3종 |
| 04 | Black Friday Traffic Flood | 300s | 4종 |
-->

PR: {{SCENARIOS_PR_URL}}
스크립트: `{{RUNNER_REPO}}/scenarios/services/{{TESTBED_NAME}}/scripts/`

---

## 5. 알람 정책 (Phase 10)

### 공통 정책 ({{COMMON_POLICY_COUNT}} 개)

{{COMMON_POLICIES_TABLE}}

### 개별 알람 (주요)

{{INDIVIDUAL_ALARMS_TABLE}}

<!--
| 자원 | measurement | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|---|
| order-service | apm.response_time_avg | 2000ms | 3000ms | 5000ms |
| postgres@rca-testbed-v2 | dpm.lock_count | 15 | 30 | 60 |
| ... |
-->

상세: `runs/{{RUN_ID}}/alarms.json`

---

## 6. Closed-loop Verify (Phase 11)

{{VERIFY_SECTION}}

<!--
attempt 1 (2026-04-30T16:10:00Z): PARTIAL
  - scenario-02 missed: ["DPM Lock 수 급증 (≥40 Lock)"]
retune (2026-04-30T16:18:00Z):
  - DPM Lock 수: LEVEL3 40 → 25
attempt 2 (2026-04-30T16:25:00Z): PASS
  - 모든 시나리오 PASS

총 verify 시간: 25 분
최종: PASS @ attempt 2
-->

---

## 7. 한계 + 알려진 부작용

- {{LIMITATIONS_BULLETS}}

<!--
- 시나리오 03 (CPU throttle) cleanup 시 KCM postgres 개별 알람 disable 됨. 콘솔에서 재활성화 필요.
- 시나리오 04 (traffic flood) cleanup 시 WPM 에이전트 재등록. 기존 disabled 에이전트 누적.
-->

---

## 8. 다음 단계 (사용자 권고)

1. Polestar10 web UI 에서 자원 상태 (UP/DOWN) 직접 확인: `{{P10_BASE_URL}}`
2. rca-scenario-runner UI 에서 시나리오 실행: `http://{{TARGET_HOST}}:8091/`
3. 추가 시나리오 필요 시: `/testbed-generate-scenarios "{{TESTBED_NAME}} 에 ..."`
4. 알람 임계치 재튜닝: `/testbed-tune-alarms "{{TESTBED_NAME}} ..."`
5. 정리 시: ansible cleanup 또는 `kubectl delete ns {{NAMESPACE}}` + testbed-polestar10-register 시나리오 4

---

## 9. 사용한 자산 (재현용)

- 인벤토리: `runs/{{RUN_ID}}/inventory.yml` (보존)
- Architecture: `runs/{{RUN_ID}}/architecture.md`
- Scenarios PR: {{SCENARIOS_PR_URL}}
- Alarms: `runs/{{RUN_ID}}/alarms.json`
- Verify log: `runs/{{RUN_ID}}/verify.log`

본 보고서: `~/.testbed-build/reports/{{RUN_ID}}-{{TESTBED_NAME}}.md` (영구)

---

## Appendix: Learnings

본 run 에서 발견한 반복 가능 패턴은 `~/.testbed-build/learnings.md` 에 누적됩니다 (Phase later).
```

---

## 변환 알고리즘

```python
# pseudo
template = read("finalize-report-template.md")
manifest = yaml.load(f"runs/{RUN_ID}/manifest.yaml")
register = json.load(f"runs/{RUN_ID}/register.json")
scenarios = json.load(f"runs/{RUN_ID}/scenarios.json")
alarms = json.load(f"runs/{RUN_ID}/alarms.json")
verify_log = read(f"runs/{RUN_ID}/verify.log")

substitutions = {
    "RUN_ID": manifest.run_id,
    "TESTBED_NAME": manifest.testbed_name,
    "TARGET_HOST": manifest.target_host,
    "STARTED_AT": manifest.created_at,
    "FINISHED_AT": manifest.last_updated_at,
    "FINAL_VERDICT": last_attempt(verify_log).overall,
    # ...
    "REGISTER_TABLE": render_register_table(register),
    "SCENARIOS_TABLE": render_scenarios_table(scenarios),
    "COMMON_POLICIES_TABLE": render_common_policies(alarms.policies),
    "INDIVIDUAL_ALARMS_TABLE": render_individual_alarms(alarms.individual_alarms),
    "VERIFY_SECTION": render_verify_log(verify_log),
    "LIMITATIONS_BULLETS": collect_warnings(scenarios),
}

report = template.format(**substitutions)
write(f"~/.testbed-build/reports/{RUN_ID}-{manifest.testbed_name}.md", report)
```

## 사용자에게 표시

```
=== 테스트베드 구축 완료 ===

최종 verdict: PASS
보고서: ~/.testbed-build/reports/2026-04-30-153022-plopvape-shop-v2.md

(보고서 핵심 요약 표시 — 위 템플릿의 "## 요약" 섹션)

다음 단계 안내:
- Polestar10 web UI: https://198.51.100.96
- 시나리오 runner: http://203.0.113.109:8091/
- 추가 시나리오: /testbed-generate-scenarios "..."
```

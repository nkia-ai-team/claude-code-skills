---
name: testbed-tune-alarms
description: NKIA RCA 테스트베드 (또는 일반 Polestar10 환경) 의 알람 임계치를 SRE 관점에서 점검·재튜닝. 메트릭 수집 → sre-baseline + 도메인 특성으로 권고 임계치 LLM 추론 → 사용자 승인 → testbed-polestar10-register 호출하여 정책 등록. 단독 호출 1급 — "/testbed-tune-alarms", "알람 임계치 점검", "APM 알람 다시 봐줘", "<service> 알람 정책 튜닝" 같은 요청 시 트리거. testbed-build 의 8번 단계가 이를 dispatch.
---

# testbed-tune-alarms

## Overview

이 스킬은 **알람 임계치 결정자**. 직접 Polestar10 API 호출 X — 권고 정책을 yaml 로 산출 → `testbed-polestar10-register` (시나리오 2) 에게 등록 dispatch.

3가지 입력으로 임계치 결정:
1. **흐르는 메트릭** — Polestar10 API 로 N분 수집한 분포 (p50/p95/p99)
2. **sre-baseline** — `infra/testbed/alert-policies/sre-baseline.md` 의 SRE 권고 표
3. **서비스 도메인 특성** — service-spec.yaml 의 description / 비즈니스 메타

---

## 입력 슬롯

| 슬롯 | 자동 결정 | 사용자 인터뷰 |
|---|---|---|
| `target_scope` | service-spec.yaml 1개면 그 testbed | "어느 testbed/서비스그룹?" |
| `domain_filter` | default 전체 (`APM/DPM/KCM/SMS`) | "특정 도메인만?" |
| `mode` | `propose` (기본, 등록 X) 또는 `apply` (등록 O) | 사용자 prompt |
| `collection_window_min` | default 10분 | "메트릭 수집 시간?" (장기 트렌드 보려면 60+) |
| `policy_kind` | 자동 (도메인별 공통 정책 + 핫 자원 개별 알람) | "공통/개별 어느 쪽?" |

---

## CRITICAL: First Step — Polestar10 부트스트랩

매 호출 첫 단계 ([testbed-polestar10-register/SKILL.md](../testbed-polestar10-register/SKILL.md) 의 부트스트랩 패턴 동일):

1. `~/.polestar10rc` 존재 확인
2. 없으면 인터뷰 (URL / USER / PASS / chmod 600)
3. `source ~/.polestar10rc`
4. recipes/login.md 실행 → 쿠키 jar 확보

이미 같은 세션에서 testbed-polestar10-register 가 부트스트랩 했다면 쿠키 재사용.

---

## 🚫 강제 룰 — "기본 정책 있으니 skip" 분기 절대 X

P10 인스턴스에 시스템 사전 생성 default 정책이 존재해도 (`PostgreSQL/APM/KCM/Network/Server` 기본 임계치 등 15여종) **무시하고 testbed 전용 정책을 항상 새로 add**. 이유:

- **시스템 default 정책의 tagValue=null** → testbed 자원의 `alarmPolicyTagValue=<testbed_name>` 와 매칭 X → 자원에 자동 적용 0건
- **자원 ↔ 정책 매핑은 tagValue 동등성으로만 작동** — 정확히 일치해야 발동
- **새 정책 add 가 정상 흐름** (`/api/alarm/policys/add` 1급 endpoint). default 정책 update 보다 단순.

→ 본 스킬은 propose / apply 분기와 무관하게 **항상 테스트베드 전용 새 정책 add 시퀀스**로 진입. `testbed-polestar10-register` 의 [scenario_2_alarm_policy.md § 강제 룰](../testbed-polestar10-register/references/scenario_2_alarm_policy.md) 참조.

회피 패턴 (절대 금지):
- "기본 정책 있어서 추가 불필요" → context 한도 / 시간 부족 핑계로 skip
- "기존 정책 update endpoint 없어서" → fallback 으로 사용자 수동 안내 후 종료
- "tagValue 매핑 안 되니 manual_action_recommended 표시 후 종료"

위 분기 발견 시 즉시 add 시퀀스 (Step 5 policy yaml 합성 → Step 7 apply) 로 복귀. 사용자 메모리 [feedback_solve_independently.md](/home/sjbang/.claude/projects/-home-sjbang-dev/memory/feedback_solve_independently.md) 의 "끝까지 자립" 룰 적용.

---

## Dispatch Flow

### 1. target_scope 결정

```
<RUNNER_ROOT>/scenarios/services/ 스캔
  RUNNER_ROOT = bootstrap.yaml 의 paths.scenario_runner_repo (사용자별 결정)
  1개 → 자동
  여럿 → 사용자 prompt
사용자 직접 servicegroup 명시 가능 (rca-scenario-runner 와 무관한 일반 케이스)
```

### 2. 메트릭 수집

[references/metric-collection.md](references/metric-collection.md) 가이드 따라 Polestar10 API 호출.

핵심:
- 도메인별 메트릭 카탈로그 endpoint 조회 (`/api/measurement/metric/{domain}`)
- 자원별 시계열 fetch (`from=NOW-Nmin&to=NOW`)
- p50/p95/p99 + max + 표준편차 계산

수집 결과 → `~/.testbed-build/runs/<ts>/metrics-snapshot.json` 또는 일시 변수.

### 3. 현재 정책 조회

```
GET /api/alarm/policys
GET /api/alarm/individuals (개별 알람)
```

→ 자원 × 메트릭 별 현재 임계치 매핑 작성.

### 4. 권고 임계치 결정 (LLM 추론)

[references/tune-prompt.md](references/tune-prompt.md) 의 prompt 템플릿 인라인으로 LLM 호출 (또는 무거운 케이스는 testbed-engineer agent 위임 가능).

입력:
- 메트릭 분포 (p50/p95/p99)
- sre-baseline 의 LEVEL1~4 표
- 서비스 도메인 (예: 결제·정산 / 주문·재고 / 검색·조회)
- 현재 적용된 임계치

출력 (LLM):
- 메트릭별 권고 LEVEL1~4
- 변경 사유 (한 줄)

### 5. policy yaml 합성

[references/policy-yaml-schema.md](references/policy-yaml-schema.md) 형식. testbed-polestar10-register 가 입력으로 받음.

### 6. 사용자 승인 ⛔ (AskUserQuestion)

권고 임계치 표 사용자에게 표시 후:

```
=== 알람 임계치 권고 ===

[plopvape-shop / APM 도메인]
서비스: order-service
  measurement: 평균응답시간
    현재:    LEVEL1=2s LEVEL2=3s LEVEL3=5s LEVEL4=10s
    권고:    LEVEL1=1s LEVEL2=2s LEVEL3=3s LEVEL4=5s
    근거:    p95=820ms / p99=1.4s. 결제 도메인 SLA 강함. 보수적 임계치 권고.

[plopvape-shop / DPM 도메인]
DB: postgres
  measurement: Lock 수
    현재:    (정책 없음 — 신규)
    권고:    LEVEL2=15 LEVEL3=30 LEVEL4=60
    근거:    평소 lock 5~10. 트랜잭션 도메인이라 baseline 보수적.

총 12개 변경 / 3개 신규 정책.
```

```python
AskUserQuestion(questions=[
  {
    "question": "위 임계치 권고를 Polestar10 에 적용할까요?",
    "header": "정책 승인",
    "multiSelect": False,
    "options": [
      {"label": "전부 적용 (Recommended)", "description": "testbed-polestar10-register 시나리오 2 dispatch"},
      {"label": "수정 후 적용", "description": "특정 권고 제외/조정 후 적용 (자유 입력)"},
      {"label": "보고서만 (propose)", "description": "yaml 만 산출, 폴스타10 등록 X"},
      {"label": "취소", "description": "권고 폐기"}
    ]
  }
])
```

### 7. mode 에 따라 분기

#### mode = propose
정책 yaml 을 사용자에게 보여주고 종료. 등록 X.

#### mode = apply (또는 사용자 yes)
testbed-polestar10-register 호출:

```
Skill: testbed-polestar10-register
  intent: "알람 정책 등록 (시나리오 2)"
  policy_yaml_path: <path>
```

testbed-polestar10-register 가 시나리오 2 dispatch flow ([scenario_2_alarm_policy.md](../testbed-polestar10-register/references/scenario_2_alarm_policy.md)) 따라 공통 정책 + 개별 알람 등록.

### 8. 등록 결과 확인

```
GET /api/alarm/policys
GET /api/alarm/individuals
```

→ 새 정책이 보이는지 확인. 없으면 errorCode 분석 → ask-polestar10 호출.

---

## Polestar10 에러 처리 표준 패턴

Polestar10 API 호출 실패 (errorCode != 0 또는 HTTP 5xx) 시:
1. recipe md 의 ## UI Fallback 섹션 먼저 확인
2. 그래도 막히면:
   ```
   Skill: ask-polestar10
     question: "<API> 가 <code> 반환. 매뉴얼에서 어디 보면 좋을까?"
   ```
3. 자동 복구 가능하면 1회 재시도
4. 그래도 실패 → 사용자에게 그대로 표시

---

## 단독 호출 예시

```
사용자: /testbed-tune-alarms "plopvape-shop APM 알람 점검"

스킬:
  1. target=plopvape-shop, domain=APM
  2. ~/.polestar10rc 부트스트랩
  3. 10분 메트릭 수집
  4. 현재 정책 조회: order/inventory/payment/product/notification 각각 평균응답시간 알람 정책 있음
  5. 분포 분석:
     order   p95=820ms  p99=1.4s
     payment p95=2.1s   p99=4.3s
     ...
  6. 권고:
     order   LEVEL3 5s → 3s (p99 의 2.5배 권고에 비해 현재 너무 관대)
     payment LEVEL3 5s → 6s (실제 p99 가 baseline 초과 — 도메인 특성 반영)
  7. 사용자 승인 prompt
  8. apply: testbed-polestar10-register dispatch
  9. /api/alarm/policys 응답에서 변경 확인
```

---

## Resources

- [metric-collection.md](references/metric-collection.md) — Polestar10 메트릭 API 카탈로그 + 수집 패턴
- [policy-yaml-schema.md](references/policy-yaml-schema.md) — 출력 yaml 스키마
- [tune-prompt.md](references/tune-prompt.md) — LLM 추론 prompt 템플릿
- [sre-baseline.md](../../infra/testbed/alert-policies/sre-baseline.md) — prior knowledge
- [testbed-polestar10-register scenario 2](../testbed-polestar10-register/references/scenario_2_alarm_policy.md) — 등록 dispatcher

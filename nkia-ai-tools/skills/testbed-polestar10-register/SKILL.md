---
name: testbed-polestar10-register
description: Polestar10 (NKIA AIOps) 관리대상 등록·정리·알람 설정 오케스트레이터. "polestar10 등록" / "자원 묶어 올려줘" / "자원 삭제" / "알람 정책 추가" 요청 시 트리거. ~/.polestar10rc 자동 부트스트랩 + 리소스 타입 (서버/DB/APM/WPM/K8s/NMS/Web URL) 별 recipe dispatch (9 recipe). testbed-build 의 polestar10_register phase + testbed-tune-alarms 가 dispatch.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(curl:*), Bash(jq:*), Bash(yq:*), Bash(grep:*), Bash(awk:*), Bash(sed:*), Bash(cat:*), Bash(tee:*), Bash(date:*), Bash(echo:*), Bash(printf:*), Bash(test:*), Bash(chmod:*), Bash(mkdir:*), Bash(head:*), Bash(tail:*), Bash(tr:*)
---

# testbed-polestar10-register

## Overview

polestar10 인스턴스에 테스트베드 자원을 **인터뷰 기반** 으로 등록·관리하는 오케스트레이터.
recipe 가 아니라 **dispatcher** — 직접 API 를 호출하지 않고, `Read` 로 recipe md 를 가져와 bash 블록을 추출한 뒤 `Bash` 로 실행한다.

**의존 recipe** (전부 [knowledge/polestar10/api/recipes/](../../knowledge/polestar10/api/recipes/)):
- `login.md` · `list-targets.md` · `list-groups.md` · `service-group-tag.md`
- `add-target.md` · `delete-target.md` · `wpm-enable-auto-add.md`
- `add-alert-policy.md` · `anomaly-policy.md` · `slo.md`

핸드오프 설계 가이드라인은 [knowledge/polestar10/api/README.md "오케스트레이터 빌더용 핸드오프 노트"](../../knowledge/polestar10/api/README.md) 참조.

---

## CRITICAL: First Step — Session Bootstrap

매 세션 첫 호출 시 반드시 다음 순서:

1. **`~/.polestar10rc` 존재 여부 체크** — `[ -f ~/.polestar10rc ] && cat ~/.polestar10rc`
2. **없으면 인터뷰 → 작성**:
   - polestar10 URL 선택 (NKIA dev / 자유 입력)
   - URL 검증
   - `POLESTAR10_USER` / `POLESTAR10_PASS` 입력
   - 파일 생성 + `chmod 600`
3. **있으면 `source ~/.polestar10rc`** 로 환경 주입.
4. **`recipes/login.md` 실행** → 쿠키 jar 확보.

상세 흐름은 [bootstrap.md](references/bootstrap.md) 참조.

---

## Resource Type Catalog

사용자가 "어떤 리소스?" prompt 에 응답할 때 보여줄 선택지. 각 항목은 dispatcher 가 어느 recipe·payload 변형으로 라우팅할지를 결정한다.

| # | 라벨 | 모델 | register endpoint | 식별자 | recipe 상태 |
|---|---|---|---|---|---|
| 1 | 서버 (Linux/Windows) | agent-based (SMS) | `/api/sms/standby-hosts/register` | `agentId` (`MA_<host>_<ts>`) | |
| 2 | 데이터베이스 (PG/MySQL/Oracle/Tibero/Cubrid/MariaDB/SQL Server) | **DB-direct** (별도 패턴) | **`/api/dpm/preregister` → `/api/dpm/register`** (단일 호출) | `resourceId` (numeric) | **확정 — [dpm-lifecycle.md](../../knowledge/polestar10/api/recipes/dpm-lifecycle.md)** |
| 3 | APM / WPM (애플리케이션) | agent-based (service+agent 2-level) | `/api/apm/standby-agent/register` (array) | `serviceName` + `agentId` + `resourceId` | |
| 4 | 쿠버네티스 (KCM) | agent-based (cluster 단위) | `/api/kcm/standby-clusters/register` (array) | `clusterId` (`cluster-<uuid>`) | |
| 5 | NMS 네트워크 | **SNMP-polling** (사용자 입력 + 3-step) | `/api/nms/v1/pre/addResource` → `/api/nms/v1/addResource` | `resourceId` (24-hex) | — [nms-lifecycle.md](../../knowledge/polestar10/api/recipes/nms-lifecycle.md) |
| 6 | Web URL | config-only | `/api/weburl/save` → `/api/weburl/register` | `weburl_<id>` | |
| 7 | 사용자정의 (SLO/Syslog/SQL/SNMP OID) | config-only | `/api/cm/slo/register/standby` 등 | type 별 | SLO / 나머지 |

**TBD 타입 처리**: recipe 가 미확정인 경우 [add-target.md "다른 agent-based 타입 확정 절차"](../../knowledge/polestar10/api/recipes/add-target.md) 와 UI fallback 안내를 그대로 사용자에게 표시.

---

## Interview Flow

사용자 요청 → 의도 분류 → 해당 시나리오로 dispatch.

```
"등록" 키워드   → 시나리오 1 (전체 테스트베드) 또는 단일 리소스 추가
"알람" 키워드   → 시나리오 2 (알람 정책 추가, 공통/개별 분기)
"그룹"/"분류"    → 시나리오 3 (서비스 그룹)
"삭제"/"정리"    → 시나리오 4 (자원 삭제 + 재출현 가드)
```

각 시나리오의 dispatch flow 는 [references/](references/) 참조:
- [scenario_1_full_testbed.md](references/scenario_1_full_testbed.md) — 신규 테스트베드 구축, 다수 자원 일괄 등록
- [scenario_2_alarm_policy.md](references/scenario_2_alarm_policy.md) — 알람 정책 추가 (공통 정책 / 개별 알람 정의)
- [scenario_3_service_group.md](references/scenario_3_service_group.md) — 서비스 그룹 신규 생성 + 자원 이동
- [scenario_4_resource_cleanup.md](references/scenario_4_resource_cleanup.md) — 자원 삭제 + agent 재출현 가드

### Common interview slots

리소스 등록 시 아래 슬롯을 차례대로 채움 (이미 답이 있으면 skip):

| 슬롯 | 기본값 | 출처 |
|---|---|---|
| **시스템 그룹** (`groupId`) | `1` (Default) | `recipes/list-groups.md` 응답 |
| **서비스 그룹** (`serviceGroupTagValue`) | (선택, 없으면 null) | `recipes/service-group-tag.md` |
| **수집 정책** (`collectorPolicyTagValue` / `dataPolicy`) | `"defaultPolicy"` | hard-coded default |
| **이상감지 정책** (`anomalyPolicyTagValue`) | `"성능 이상감지 기본 정책"` | `recipes/anomaly-policy.md` 응답 |
| **알람 정책 추가 여부** | (선택, 별도 단계) | `recipes/add-alert-policy.md` |

> 슬롯 캐싱: 같은 세션 안에서 이미 사용자가 답한 값은 재질문하지 않는다. `recipes/list-groups.md`, `cm/tag/key/list`, `aiops/v1/anomaly-policies/names` 응답은 세션 캐시 (handoff note §5).

---

## Recipe Dispatch Pattern

각 작업마다 동일한 4단계 dispatch:

```
1. recipe md 파일 Read   → bash 블록 추출
2. 필요한 슬롯 값 주입    → 환경변수 또는 jq --arg 로 치환
3. Bash 툴로 실행         → 응답 JSON 캡처
4. success/errorCode 체크 → 실패 시 recipe 의 ## UI Fallback 섹션을 사용자에게 그대로 표시
```

식별자는 placeholder 값을 그대로 쓰지 않고 **API 응답에서 동적 획득** (handoff note §3):
- `AGENT_ID` ← `sms/standby-hosts-filter-step1` 응답의 `content[].agentId`
- `WURL_ID` ← `weburl/save` 응답의 `data.id` 또는 `weburl/list-filter` 의 `content[].id`
- `groupId` ← `cm/groups/list` 사용자 선택
- `serviceGroupTagValue` ← 사용자 입력 또는 `cm/tag/value/insert` 사전 생성

---

## API Response Preprocessing — jq Filter (LLM 컨텍스트 절약)

**룰**: 모든 API 응답을 LLM 컨텍스트에 그대로 넣지 X. `jq` 로 필요한 필드만 추출 후 bash 변수 또는 짧은 요약만 LLM 에 전달.

### Anti-pattern (LLM 컨텍스트 폭증)

```bash
# ❌ 안티패턴 — 응답 전체 (수십 KB JSON) 가 LLM 컨텍스트로 들어옴
RESP=$(curl ... /api/sms/standby-hosts-filter-step1)
echo "$RESP"   # LLM 이 이걸 읽고 agentId 파싱
```

### 올바른 패턴

```bash
# ✅ jq 로 필요한 필드만 추출 — LLM 에는 추출된 값만 전달
RESP=$(curl ... /api/sms/standby-hosts-filter-step1)
AGENT_ID=$(echo "$RESP" | jq -r '.content[0].agentId')
RESOURCE_ID=$(echo "$RESP" | jq -r '.content[0].resourceId')
echo "extracted: agentId=$AGENT_ID resourceId=$RESOURCE_ID"   # LLM 에는 이것만
```

### 다중 항목 — array 일괄 처리

여러 항목 등록 시 jq 로 **register payload 직접 합성** 후 curl body 에 전달 (LLM 이 배열 변환 X):

```bash
# WPM step2 응답 → register 대상만 추출 + 필요 필드 추가
REG_PAYLOAD=$(echo "$STEP2_RESP" | jq --arg svc "$TESTBED_NAME" '
  [ .data.content[]
    | select(.serviceName | startswith($svc))
    | { serviceName, agentId, resourceId, confId, category,
        managementStatus: "MANAGED",
        collectorPolicyTagValue: "defaultPolicy",
        groupId: 1 } ]')
curl ... -d "$REG_PAYLOAD" /api/apm/standby-agent/register
```

### 추출 대상 표준 패턴

| 응답 종류 | jq filter | 추출 후 LLM 에 전달 |
|---|---|---|
| `content[]` (페이지네이션) | `.content[0].fieldName` 또는 `.content[] | select(.cond) | .field` | 단일 ID 또는 짧은 요약 |
| `data.id` (단건) | `.data.id` | ID 한 개 |
| `data[]` (다건) | `[.data[] | {field1, field2}]` | 짧은 array |
| 에러 응답 | `.errorCode // "ok"` | 에러 코드 한 단어 |

### Verbose log 는 LLM 외부에 저장

전체 응답이 디버깅에 필요하면 LLM 컨텍스트가 아닌 파일에:

```bash
RESP=$(curl ... /api/...)
echo "$RESP" > "$RUN_DIR/api-response-$(date +%s).json"   # 디스크 저장
EXTRACT=$(echo "$RESP" | jq -r '.errorCode // "ok"')
[ "$EXTRACT" != "ok" ] && echo "ERROR — see $RUN_DIR/api-response-*.json"
```

LLM 은 추출된 필드만 보고 reasoning. 디버깅 시 사용자 또는 LLM 이 "Read $RUN_DIR/api-response-...json" 으로 명시적 요청 시에만 컨텍스트에 적재.

---

## Idempotency & Verification

오케스트레이터가 같은 작업이 두 번 호출돼도 안전하게 (handoff note §4):

- **등록 전**: `count` / `list-filter` 로 같은 이름의 항목이 이미 존재하는지 체크 → 있으면 사용자에게 skip 또는 update prompt.
- **등록 후**: `list-filter` 로 새 항목이 보이는지 검증 (각 recipe 의 "검증" 섹션).
- **삭제 전후**: `count` 비교로 실제 감소 확인.
- **agent-based 삭제 후**: heartbeat 사이클 (5~10분) 안에 standby 재출현 가능 → 시나리오 4 의 재출현 가드 흐름 사용.

---

## Error Handling

recipe 응답 패턴별 처리는 핸드오프 노트 §6 표를 그대로 사용:

| 응답 | 처리 |
|---|---|
| `success:true` | 다음 단계 |
| `success:false`, `errorCode:"POLESTAR_xxxx"` | `errorMsgArgs` 사용자에게 표시 + UI fallback 제안 |
| HTTP 401/403 + HTML 본문 | `recipes/login.md` 재실행 (세션 만료) |
| HTTP 404 | recipe 가 outdated → follow-up 이슈 안내 |
| 연결 거부 / 타임아웃 | `POLESTAR10_BASE_URL` 재확인 prompt |

> recipe 자체가 self-documenting (각 파일에 `## 실패 시나리오` + `## UI Fallback`) — 오케스트레이터는 분류만 하고, 본문은 recipe 의 것을 그대로 인용.

---

## What This Skill Does NOT Do

- **API 호출 코드 작성** — 모두 recipe 가 담당
- **메트릭 카탈로그 / severity / 도메인 dropdown 정적 보유** — 런타임에 동적 조회 (`measurement/definitions/resource-type` 등)
- **MFA TOTP 자동화** — MFA 활성 계정은 recipe 가 중단하고 UI fallback 안내
- **에이전트 설치/제거** — 이 스킬은 polestar10 web API 만. 에이전트 라이프사이클은 별도 sub-skill 영역
- **자원 단위 담당자/권한 부여** — 테스트베드 구축 자동화 범위 밖. 필요 시 UI 에서 직접 (`전체구성 > 관리대상 > 행 선택 > 권한 패널`)

---

## Resources

- [bootstrap.md](references/bootstrap.md) — 세션 부트스트랩 (rc 파일 셋업, URL 검증, 로그인) 상세 절차
- [scenario_1_full_testbed.md](references/scenario_1_full_testbed.md) — 신규 테스트베드 구축
- [scenario_2_alarm_policy.md](references/scenario_2_alarm_policy.md) — 알람 정책 추가 (공통/개별)
- [scenario_3_service_group.md](references/scenario_3_service_group.md) — 서비스 그룹 생성 + 자원 이동
- [scenario_4_resource_cleanup.md](references/scenario_4_resource_cleanup.md) — 자원 삭제 + 재출현 가드
- [knowledge/polestar10/api/README.md](../../knowledge/polestar10/api/README.md) — recipe 사용 정책, 인스턴스 목록, 핸드오프 노트
- [knowledge/polestar10/api/endpoints.md](../../knowledge/polestar10/api/endpoints.md) — 전체 endpoint 표

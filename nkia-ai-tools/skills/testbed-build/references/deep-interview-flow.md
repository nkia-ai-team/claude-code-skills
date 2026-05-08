# Deep Interview — 새 testbed 생성 (옵션 3 전용)

**조건부 적용**: Phase 1-A 묶음에서 사용자가 옵션 3 (새 testbed 생성) 선택 시에만 read. 옵션 1 (기존 plopvape-shop) / 옵션 2 (다른 기존 testbed) 면 본 reference 자체 skip.

옵션 3 deep interview 결과는 services-author 가 코드 생성 입력으로 사용.

> 🎯 **흐름 원칙**: 사용자에게 **도메인 선택만** 받고, 나머지 (이름 / 서비스 분할 / DB 스키마 / failure_surfaces) 는 **LLM 이 도메인 보고 자동 제안**. 사용자는 종합 spec 검토 + 일부 수정만. 사용자가 이름 검사부터 받는 흐름 X.
>
> 🚫 **턴 분리 강제**: 자유 입력과 AskUserQuestion 카드는 절대 같은 턴에 발사 X. interview-flow.md § 강제 규칙 참조.

## 2-d-a. 도메인 선택 (턴 1 — AskUserQuestion 단독)

deep interview 의 **첫이자 거의 유일한 사용자 입력**. 나머지는 LLM 자동 제안 후 검토.

### Step 1: testbed-services 레포 스캔

기존 testbed 와 도메인 충돌을 피하기 위해 LLM 이 testbed-services 레포의 top-level 디렉토리 목록을 먼저 확인:

```bash
ls -d "$TESTBED_SERVICES_REPO"/*/ | xargs -n1 basename | grep -v "^\.\|^node_modules"
```

각 디렉토리의 README.md (있으면) 또는 디렉토리 이름으로 어떤 도메인이 이미 커버되는지 추론. 예: `plopvape-shop` 발견 → e-commerce 가 이미 있다고 판단.

### Step 2: LLM 이 미커버 도메인 1개 자동 추천

이미 커버된 도메인 (e-commerce 등) 을 제외하고, RCA 검증에 의미 있는 미커버 도메인 1개를 LLM 이 추천. 후보 풀 (banking / IoT / 소셜 피드 / 물류 / 의료 예약 / 푸드 딜리버리 / SaaS 멀티테넌트 / 메시징 등) 중에서 testbed-services 에 없는 것을 우선 선택.

### Step 3: 추천 + Other 두 옵션 카드

```python
AskUserQuestion(questions=[
  {
    "question": "이 testbed 가 어떤 도메인을 시연하면 좋을까요? testbed-services 레포에 이미 있는 변형 (예: e-commerce 의 plopvape-shop) 과 겹치지 않는 도메인을 LLM 이 한 가지 추천해 드렸습니다. 추천을 그대로 쓰거나, 다른 도메인을 직접 입력하실 수 있어요.",
    "header": "테스트베드 도메인",
    "multiSelect": False,
    "options": [
      {"label": "{{LLM_RECOMMENDED_DOMAIN}} (Recommended)", "description": "{{LLM_RECOMMENDED_REASON}} — 예: '소셜 피드 — testbed-services 에 fan-out / cache 패턴이 아직 없어서 RCA 검증 다양성에 도움'"}
    ]
  }
])
```

옵션 1개 + AskUserQuestion 자동 추가 `Other`. 사용자가 Other 선택 시 별 턴에 텍스트 prompt:

```
testbed 가 시연할 도메인을 알려주세요 (한 줄 설명, 예: "음식 배달 주문 처리 시스템" 또는 "의료 예약").
```

(testbed-services 와 도메인 충돌 검사 — 같은 분야면 LLM 이 차별점 제안: "기존 plopvape-shop 이 e-commerce 라 충돌. multi-tenant 분기로 차별화할까요?")

## 2-d-b. LLM 자동 제안 (턴 2 — 인터뷰 X, 출력만)

도메인 받자마자 LLM 이 다음 5가지를 한 번에 합성:

1. **testbed 이름** — kebab-case, testbed-services 레포 충돌 검사 자동 (충돌 시 `-v2` 등 자동 변형). 예: 은행 → `core-banking`, IoT → `iot-platform`, 음식 배달 → `food-delivery`
2. **서비스 분할** — 4~6개 microservice (이름 + 책임 + endpoints + depends_on)
3. **DB 종류** — 도메인 적합 default (트랜잭션 도메인이면 PostgreSQL)
4. **DB 스키마** — service 분할 보고 테이블 + 컬럼 + PK/FK 합성
5. **failure_surfaces** — default 4종 (db-lock-contention / external-api-timeout / db-cpu-throttle / traffic-flood)
6. **APM 도구** — default OTel + WPM Scouter dual-attach (6종 에이전트 풀 스택 모니터링). 사용자가 OTel only 원하면 명시 요청

**사용자에게 종합 spec 표시** (인터뷰 X, 알림만):

```
=== LLM 자동 제안 spec ===

이름:    core-banking
도메인:  은행/금융
서비스:  account, transfer, ledger, audit (4)
  - account:  계좌 조회/잔액 (GET /api/accounts/{id})
  - transfer: 이체 실행 (POST /api/transfer) [depends: account]
  - ledger:   거래 내역 (GET /api/ledger/{accountId}) [depends: transfer]
  - audit:    감사 이벤트 (POST /api/audit/event)
DB:       PostgreSQL + 4 테이블 (accounts, transfers, ledger, audit_events)
APM 도구:  OTel + WPM Scouter dual-attach (default — 6종 에이전트 풀 스택 모니터링)
          OTel only 만 원하면 다음 카드의 'Other' 로 'OTel only' 응답
시나리오: db-lock-contention / external-api-timeout / db-cpu-throttle / traffic-flood

services-author 가 testbed-services 레포에 다음 작업 진행 예정:
  - feat/core-banking-scaffold 브랜치 생성
  - core-banking/ 디렉토리 + 4 service module + shop-common
  - db/init.sql + k8s/ 매니페스트 + docker-compose.dev.yml
  - mvnw clean package 검증
  - PR 생성
```

이름 충돌 시 (testbed-services 에 동일 이름 디렉토리 존재) LLM 이 자동으로 `-v2` 또는 다른 변형 제안 (사용자에게 안 묻고 자동).

## 2-d-c. 사용자 검토 + 승인 (턴 3 — AskUserQuestion 단독)

```python
AskUserQuestion(questions=[
  {
    "question": "위 spec 으로 services-author 를 진행할까요?",
    "header": "최종 승인",
    "multiSelect": False,
    "options": [
      {"label": "이대로 진행 (Recommended)", "description": "PR push_mode=pr 로 자동 생성 (APM=OTel + WPM dual-attach, 6종 풀 스택)"},
      {"label": "이름만 다시", "description": "이름이 마음에 안 듦 — 자유 입력으로 직접 선택 (kebab-case 검증)"},
      {"label": "서비스 분할 수정", "description": "서비스 추가/제거/이름변경/endpoint 조정"},
      {"label": "DB 종류 변경", "description": "PostgreSQL 외 6종 (MySQL/MariaDB/Oracle/Tibero/CUBRID/SQL Server) 선택"}
    ]
  }
])
```

`Other` 옵션은 AskUserQuestion 자동 추가 — "취소 / 다른 항목 변경" 자유 입력 fallback. 예시:
- `OTel only` 또는 `WPM 빼고` → manifest_requirements.wpm_jvm_attach=false 로 services-author 진행. WPM 부착 X (단 RCA 검증 시 WPM 메트릭 알람은 제외됨 — Scouter TX queue / GC profiling 등). default 는 dual-attach 라 6종 풀 스택.
- `취소` → run 종료, manifest 미작성

## 2-d-d. 수정 분기 (턴 4+, 사용자가 수정 선택 시만)

수정 선택 시 별 턴에 해당 항목만 입력 받고 → LLM 이 spec 반영 → 다시 2-d-c 승인 루프.

### 이름만 변경 (자유 입력 단독 턴)
```
새 이름을 입력해 주세요 (영문 kebab-case, 8~40자):
_
```
검증: kebab-case 정규식 (`^[a-z][a-z0-9-]*$`) + testbed-services 충돌 검사. 충돌 시 LLM 이 변형 제안.

### 서비스 분할 수정 (자유 입력 단독 턴)
사용자가 변경 사항 자유 입력 (예: "audit 빼고 notification 추가, transfer 의 endpoint /api/transfer/cancel 추가"). LLM 이 반영하여 spec 다시 표시 → 다시 2-d-c 승인.

### DB 종류 변경 (AskUserQuestion 단독 턴)
DPM 지원 7종 중 4개 카드 + Other (Tibero/CUBRID/SQL Server 자유 입력):
```python
AskUserQuestion(questions=[
  {
    "question": "DB 종류는 어떤 걸 사용하시겠어요? (Polestar10 DPM 모니터링 지원)",
    "header": "DB 종류",
    "multiSelect": False,
    "options": [
      {"label": "PostgreSQL (Recommended)", "description": "plopvape-shop 이 사용 중이라 검증된 경로. ARM 호환."},
      {"label": "MySQL", "description": "널리 쓰이는 OSS RDB"},
      {"label": "MariaDB", "description": "MySQL fork. 라이선스 자유"},
      {"label": "Oracle", "description": "Enterprise DB. 라이선스 / 이미지 별도 준비 필요"}
    ]
  }
])
```
선택 후 LLM 이 새 DB 에 맞게 스키마 재생성 → 다시 2-d-c 승인.

승인 시 `services_author` dispatch 진입. **사용자 입력 최소화 — 도메인 1개 선택 + (필요 시) 일부 수정** 으로 끝나는 가벼운 흐름.

## 옵션 3 산출 (interview.yaml 의 app 섹션)

```yaml
app:
  testbed_name: "core-banking"
  app_subdir: "core-banking"
  namespace: "rca-testbed-banking"
  branch: "feat/core-banking-scaffold"
  db_kind: "postgresql"
  is_new_variant: true
  domain: "은행/금융"
  services:
    - name: account
      responsibilities: ["계좌 조회", "잔액 조회"]
      endpoints:
        - {method: GET, path: "/api/accounts/{id}", description: 계좌 단건 조회}
        - {method: GET, path: "/api/accounts/{id}/balance", description: 잔액 조회}
      depends_on: []
    - name: transfer
      responsibilities: ["계좌 이체 실행"]
      endpoints:
        - {method: POST, path: "/api/transfer", description: 이체 실행}
      depends_on: [account]
    # ... ledger, audit
  db:
    kind: postgresql
    schemas:
      - table: accounts
        columns:
          - {name: id, type: "VARCHAR(64)", pk: true}
          - {name: holder, type: "VARCHAR(128)"}
          - {name: balance, type: "DECIMAL(18,2)"}
      # ... transfers, ledger, audit_events
  failure_surfaces:
    - lock-contention
    - external-timeout
    - db-cpu-throttle
    - traffic-flood
  push_mode: pr   # default
```

이 yaml 이 services-author task spec + dynamic-inventory + generate-scenarios 의 입력.

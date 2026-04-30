# 4단계 인터뷰 질문지

testbed-build Phase 1 에서 사용. 인터뷰 답은 `runs/<RUN_ID>/interview.yaml` 에 저장 + 이후 phase 들의 입력.

## 슬롯 캐싱

같은 세션 안에서 이미 답한 슬롯은 재질문 X. bootstrap.yaml 에 영구 저장된 값도 default 로 표시.

---

## 단계 (a): 타겟 서버

```
=== Step 1/4: 타겟 서버 ===

1-a. 어디에 배포? (IP / alias / hostname):
   default: 192.168.200.109 (109 DGX Spark, ARM64)
   _

1-b. SSH user [nkia]: _

1-c. SSH 인증 방식:
   1) password (인터뷰에서 입력)
   2) ~/.ssh/id_rsa (key)
   3) bootstrap.yaml 의 ssh_key_path
   선택 [1]: _

1-d. (옵션) become password (sudo) [TESTBED_PASSWORD 와 같음]: _
```

검증:
- IP 형식 (xxx.xxx.xxx.xxx) 또는 hostname 도달성 ping 1회
- 도달 X 시 사용자에게 prompt: "도달 안 됨. 진행? [y/N/edit]"

산출:
```yaml
target:
  host: "192.168.200.109"
  user: "nkia"
  auth_mode: "password" | "ssh_key"
  ssh_key_path: "/home/sjbang/.ssh/id_rsa"   # auth_mode=ssh_key 시
  arch: "arm64"   # uname -m 1회 호출로 자동 (이번 인터뷰의 fallback 슬롯)
```

> arm64 / amd64 자동 감지: `ssh <user>@<host> 'uname -m'`. 결과 aarch64/arm64 → arm64, x86_64/amd64 → amd64.

---

## 단계 (b): 배포 앱

```
=== Step 2/4: 배포 앱 ===

2-a. 어떤 testbed?
   1) plopvape-shop (레퍼런스, e-commerce 5 services + postgres)
   2) testbed-services 레포의 다른 변형 (스캔 결과: ...)
   3) 새 도메인 변형 자동 생성 (services-author dispatch)
   선택 [1]: _

2-b. K8s namespace [rca-testbed]: _
   (이미 사용 중인 namespace 면 충돌 방지 위해 -v2 등 권고)

2-c. (선택) testbed-services 레포 branch [main]: _
```

검증 (옵션 1, 2):
- 선택한 testbed 디렉토리 존재 (testbed-services 레포 안에)
- namespace 가 타겟 K8s 에서 사용 중인지 (`kubectl get ns`)

옵션 1, 2 산출:
```yaml
app:
  testbed_name: "plopvape-shop"
  app_subdir: "plopvape-shop"
  namespace: "rca-testbed-v2"
  branch: "main"
  db_kind: "postgresql"   # service-spec 또는 testbed-services k8s 매니페스트에서 추론
  is_new_variant: false
```

---

## 단계 (b-deep): 새 도메인 변형 (옵션 3 선택 시)

옵션 3 선택 시 다음 deep interview 진행. 결과는 services-author 가 코드 생성 입력으로 사용.

### 2-d-a. 새 testbed 이름

```
새 testbed 이름 (영문 kebab-case, 예: "core-banking", "iot-platform"):
_
```

검증:
- testbed-services 레포에 같은 이름 디렉토리 X
- kebab-case 정규식 매치 (`^[a-z][a-z0-9-]*$`)
- 8~40자
- 충돌 시 다시 prompt + LLM 이 변형 제안 (`-v2`, `-banking-v2`)

### 2-d-b. 도메인 분야

```
도메인 카테고리 선택 또는 자유 입력:
   1) 은행/금융 (banking) — account / transfer / ledger / audit
   2) IoT 플랫폼 — device-registry / telemetry / command / alert
   3) 소셜 피드 — post / feed / comment / notification
   4) 물류 — shipment / warehouse / route / driver
   5) 의료 예약 — appointment / patient / schedule / billing
   6) 자유 입력 (LLM 이 서비스 분할 제안)
   선택 [1]: _
```

자유 입력 시 추가 prompt: "도메인 한 줄 설명 (예: '음식 배달 주문 처리 시스템'):"

기존 testbed-services 레포의 다른 변형과 도메인 충돌 검사 — 같은 분야면 LLM 이 차별점 제안 ("plopvape-shop 이 e-commerce 라 충돌. multi-tenant 변형으로?").

### 2-d-c. 서비스 분할 LLM 제안

선택 도메인 → LLM 이 4~6개 microservice 분할 + 각 서비스 책임/endpoint 제안:

```
[LLM 제안 — core-banking]
1. account
   책임: 계좌 조회, 잔액 조회
   endpoints:
     GET  /api/accounts/{id}
     GET  /api/accounts/{id}/balance
   depends_on: []

2. transfer
   책임: 계좌 이체 실행
   endpoints:
     POST /api/transfer
     GET  /api/transfer/{id}
   depends_on: [account]

3. ledger
   책임: 거래 내역 기록 + 조회
   endpoints:
     GET  /api/ledger/{accountId}
   depends_on: [transfer]

4. audit
   책임: 감사 이벤트 수집
   endpoints:
     POST /api/audit/event (internal)
   depends_on: []

이 분할로 진행? [Y/n/edit]
```

`edit` 선택 시:
- 서비스 add (이름 + 책임 + endpoints + depends_on)
- 서비스 rename / remove
- endpoint 추가/제거
- 의존성 그래프 변경

### 2-d-d. DB 선택 (DPM 지원 7종)

```
DB 종류 (DPM 모니터링 지원):
   1) PostgreSQL ⭐ (default, plopvape-shop 이 사용 중이라 검증된 경로)
   2) MySQL
   3) MariaDB
   4) Oracle
   5) Tibero
   6) CUBRID
   7) SQL Server
   선택 [1]: _

스키마 자동 생성? [Y/n]
```

자동 생성 yes → LLM 이 service 분할 보고 DB 테이블 + 컬럼 + PK/FK 합성:

```
[LLM 제안 — core-banking schema]

CREATE TABLE accounts (
  id          VARCHAR(64) PRIMARY KEY,
  holder      VARCHAR(128) NOT NULL,
  balance     DECIMAL(18,2) NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transfers (
  id           BIGSERIAL PRIMARY KEY,
  from_account VARCHAR(64) REFERENCES accounts(id),
  to_account   VARCHAR(64) REFERENCES accounts(id),
  amount       DECIMAL(18,2) NOT NULL,
  status       VARCHAR(16) NOT NULL,
  tx_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ledger (
  id          BIGSERIAL PRIMARY KEY,
  account_id  VARCHAR(64) REFERENCES accounts(id),
  delta       DECIMAL(18,2) NOT NULL,
  ref_tx_id   BIGINT REFERENCES transfers(id),
  posted_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_events (
  id          BIGSERIAL PRIMARY KEY,
  service     VARCHAR(32) NOT NULL,
  event_type  VARCHAR(64) NOT NULL,
  payload     JSONB,
  occurred_at TIMESTAMPTZ DEFAULT NOW()
);

이 스키마로 진행? [Y/n/edit]
```

자동 생성 no → 사용자가 SQL 직접 입력 (multi-line).

### 2-d-e. failure_surfaces 결정

```
이 testbed 가 어떤 장애 패턴을 시연해야 하나요? (다중 선택 OK):
   1) ✅ db-lock-contention (DB row lock 경합)
   2) ✅ external-api-timeout (외부 의존성 무응답)
   3) ✅ db-cpu-throttle (DB CPU 제한)
   4) ✅ traffic-flood (동시성 폭주)
   5) (사용자 정의)

기본 4종 그대로 사용? [Y/n/select]
```

각 surface 의 기본 lock_table / external_container 등은 LLM 이 services + db.schemas 보고 자동 매핑 (services-author 가 이 매핑을 scenario_hints 로 반환).

### 2-d-f. 사용자 최종 승인

deep interview 결과 종합 표시:

```
=== 새 testbed 변형 요약 ===

이름:    core-banking
도메인:  은행/금융
서비스:  account, transfer, ledger, audit (4)
DB:      PostgreSQL + 4 테이블 (accounts, transfers, ledger, audit_events)
시나리오: db-lock / external-timeout / db-cpu-throttle / traffic-flood

services-author 가 testbed-services 레포에 다음 작업:
  - feat/core-banking-scaffold 브랜치 생성
  - core-banking/ 디렉토리 + 4 service module + shop-common
  - db/init.sql + k8s/ 매니페스트 + docker-compose.dev.yml
  - mvnw clean package 검증
  - PR 생성 (또는 직접 push)

진행? [Y/n/edit]
```

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

---

## 단계 (c): NMS 모니터링

```
=== Step 3/4: NMS (네트워크 장비) ===

3-a. NMS 모니터링 대상 네트워크 장비가 있나요?
   1) 없음 (skip)
   2) 있음 — IP + SNMP 자격증명 입력
   선택 [1]: _

(2 선택 시)
   장비 IP: _
   SNMP version [v2c]: _
   community string [public]: _
   ...
```

산출:
```yaml
nms:
  enabled: false   # default
  # enabled true 시:
  devices:
    - host: "192.168.x.x"
      snmp_version: "v2c"
      community: "public"
```

---

## 단계 (d): Polestar10 웹 조작 모드

```
=== Step 4/4: Polestar10 자원 등록 모드 ===

4-a. 자동 vs 직접:
   1) 자동 — testbed-polestar10-register 가 API 로 일괄 등록
   2) 직접 — Polestar10 웹 UI 로 사용자가 수동 등록 후 진행
   선택 [1]: _

(2 선택 시: testbed-build 는 등록 단계에서 사용자 안내만 하고 register 호출 skip. verify 단계 진입 전 사용자가 "등록 완료" 확인 필요.)
```

산출:
```yaml
polestar10:
  registration_mode: "auto" | "manual"
```

---

## interview.yaml 통합 산출

위 모든 답변을 합쳐:

```yaml
# runs/<RUN_ID>/interview.yaml
run_id: 2026-04-30-153022
target:
  host: "192.168.200.109"
  user: "nkia"
  auth_mode: "password"
  arch: "arm64"
app:
  testbed_name: "plopvape-shop"
  app_subdir: "plopvape-shop"
  namespace: "rca-testbed-v2"
  branch: "main"
  db_kind: "postgresql"
nms:
  enabled: false
polestar10:
  registration_mode: "auto"
```

이 yaml 이 architecture-draft / inventory generator / verify-task 의 입력.

---

## 인터뷰 변경 (resume 시)

resume 으로 phase 1 재진입 시:
```
=== 이전 인터뷰 답변 ===
target.host: 192.168.200.109
app.testbed_name: plopvape-shop
namespace: rca-testbed-v2
nms.enabled: false
polestar10.registration_mode: auto

이대로 진행? [Y/n/edit]
```

`edit` 선택 시 변경할 슬롯만 인터뷰. 나머지는 그대로.

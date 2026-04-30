# 4단계 인터뷰 질문지

testbed-build Phase 1 에서 사용. 인터뷰 답은 `runs/<RUN_ID>/interview.yaml` 에 저장 + 이후 phase 들의 입력.

## ⚠️ 도구 사용 — AskUserQuestion 필수

**모든 multi-choice 인터뷰는 텍스트 프롬프트가 아니라 `AskUserQuestion` 도구로 질문**. 사용자에게 카드형 UI 가 떠서 클릭으로 선택 가능, "Other" 옵션은 자동 추가되어 자유 입력 fallback.

순수 자유 입력만 필요한 슬롯 (target IP, namespace 이름 등) 만 텍스트 프롬프트 사용.

도구 spec:
- 1~4개 질문 묶음 가능 → **여러 단계를 한 호출에 묶어** UX 빠르게
- 옵션 2~4개 (Other 자동)
- 권고 옵션은 `(Recommended)` suffix + 첫 번째 위치
- header 12자 이내 (chip/tag)

## 슬롯 캐싱

같은 세션 안에서 이미 답한 슬롯은 재질문 X. bootstrap.yaml 에 영구 저장된 값도 default 로 표시.

추천 패턴: 4단계 인터뷰를 **Phase 1-A (1 AskUserQuestion call, 3 questions)** + **Phase 1-B (target server, 자유 입력 텍스트 프롬프트)** 두 묶음으로 진행.

---

## 추천 호출: Phase 1-A 묶음 (배포 앱 + Polestar10 모드)

NMS 질문 제거 — default 비활성 (bootstrap 안내 박스 참조). 사용자가 명시적으로 NMS 가 필요하면 testbed-polestar10-register 시나리오 1 의 NMS 분기로 별도 진행.

```python
AskUserQuestion(questions=[
  {
    "question": "어떤 testbed 를 배포하시겠어요?",
    "header": "배포 앱",
    "multiSelect": False,
    "options": [
      {"label": "plopvape-shop (Recommended)", "description": "레퍼런스 e-commerce 5 services + postgres. 가장 검증된 경로."},
      {"label": "기존 다른 변형", "description": "testbed-services 레포 안의 다른 변형 (스캔 결과 표시)"},
      {"label": "신규 도메인 변형", "description": "services-author 가 LLM 으로 새 코드 자동 생성 (deep interview 진입)"}
    ]
  },
  {
    "question": "Polestar10 자원 등록을 어떻게 진행할까요?",
    "header": "P10 모드",
    "multiSelect": False,
    "options": [
      {"label": "자동 (Recommended)", "description": "testbed-polestar10-register 스킬이 API 로 일괄 등록"},
      {"label": "직접 (수동)", "description": "사용자가 Polestar10 web UI 로 수동 등록 후 진행"}
    ]
  }
])
```

---

## 단계 (a): 타겟 서버 — 자유 입력 + multi-choice 혼합

> **타겟 서버 = 테스트베드 (K3s + 서비스 + 4 host 에이전트) 가 설치될 호스트**. Polestar10 모니터링 서버 (96/dev) 와 분리. 사용자가 헷갈리지 않게 명시.

### 1-a, 1-b: target host + user (자유 입력 — 텍스트 프롬프트)

```
=== Step 1: 타겟 서버 (테스트베드가 배포될 곳) ===

질문: "타겟 서버 IP/hostname? (default: 192.168.200.109 — 109 DGX Spark, ARM64)"
질문: "SSH user? (default: nkia)"
```

이 두 슬롯은 자유 입력이라 AskUserQuestion 부적합. 일반 텍스트 프롬프트.

> 타겟 = 109 면 default 그대로. 다른 호스트 (예: Mac multipass 또는 다른 서버) 에 깔 거면 IP 직접 입력.

### 1-c: SSH 인증 방식 (AskUserQuestion)

```python
AskUserQuestion(questions=[
  {
    "question": "SSH 인증 방식?",
    "header": "SSH 인증",
    "multiSelect": False,
    "options": [
      {"label": "Password (Recommended)", "description": "인터뷰에서 password 직접 입력. 가장 단순."},
      {"label": "SSH key", "description": "~/.ssh/id_rsa 또는 bootstrap.yaml 의 ssh_key_path"}
    ]
  }
])
```

### 1-d: become password (옵션, 자유 입력)

password 와 같으면 skip. 다르면 자유 입력 prompt.

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

## 단계 (b): 배포 앱 — 위 Phase 1-A 묶음에 포함됨

2-a (어떤 testbed) 는 위 묶음에서 처리. 이후 namespace + branch 는 자유 입력:

```
질문: "K8s namespace (default: rca-testbed-v2)?"
질문: "testbed-services branch (default: main, Enter 로 default)?"
```

namespace 가 이미 사용 중인지 검증 (`kubectl get ns`) → 충돌이면 다시 prompt.

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

### 2-d-b. 도메인 분야 (AskUserQuestion)

AskUserQuestion 은 옵션 max 4개. 인기 4개를 명시 + Other 가 자동으로 자유 입력 fallback:

```python
AskUserQuestion(questions=[
  {
    "question": "어떤 도메인의 testbed?",
    "header": "도메인",
    "multiSelect": False,
    "options": [
      {"label": "은행/금융 (Recommended)", "description": "account / transfer / ledger / audit. 트랜잭션·lock 패턴 풍부."},
      {"label": "IoT 플랫폼", "description": "device-registry / telemetry / command / alert. high-throughput / queue 패턴."},
      {"label": "소셜 피드", "description": "post / feed / comment / notification. cache / fan-out 패턴."},
      {"label": "물류", "description": "shipment / warehouse / route / driver. graph traversal / 외부 의존."}
    ]
  }
])
```

`Other` 선택 시 자유 입력 → 사용자가 도메인 한 줄 설명 (예: "음식 배달 주문 처리 / 의료 예약").

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

이 분할로 진행?
```

승인은 AskUserQuestion 으로:

```python
AskUserQuestion(questions=[
  {
    "question": "위 서비스 분할로 진행할까요?",
    "header": "서비스 승인",
    "multiSelect": False,
    "options": [
      {"label": "진행 (Recommended)", "description": "이 분할 그대로 services-author 가 코드 생성"},
      {"label": "수정 (edit)", "description": "서비스 추가/제거/이름변경/endpoint 조정 후 재제안"}
    ]
  }
])
```

`edit` 선택 시 추가 자유 입력으로 변경사항 받음 (서비스 add/rename/remove, endpoint 추가/제거, depends_on 그래프).

### 2-d-d. DB 선택 (DPM 지원 7종) — AskUserQuestion 두 묶음

DPM 지원 7종 중 4개 옵션 + Other (Tibero/CUBRID/SQL Server 등은 Other 자유 입력):

```python
AskUserQuestion(questions=[
  {
    "question": "DB 종류 (Polestar10 DPM 모니터링 지원)?",
    "header": "DB 종류",
    "multiSelect": False,
    "options": [
      {"label": "PostgreSQL (Recommended)", "description": "plopvape-shop 이 사용 중이라 검증된 경로. ARM 호환."},
      {"label": "MySQL", "description": "널리 쓰이는 OSS RDB"},
      {"label": "MariaDB", "description": "MySQL fork. 라이선스 자유"},
      {"label": "Oracle", "description": "Enterprise DB. 라이선스 / 이미지 별도 준비 필요"}
    ]
  },
  {
    "question": "DB 스키마 자동 생성?",
    "header": "스키마",
    "multiSelect": False,
    "options": [
      {"label": "자동 생성 (Recommended)", "description": "LLM 이 service 분할 보고 테이블+컬럼+PK/FK 합성"},
      {"label": "수동 입력", "description": "사용자가 SQL DDL 직접 입력"}
    ]
  }
])
```

`Other` 선택 시 Tibero/CUBRID/SQL Server 자유 입력. ARM 환경에서는 Tibero/CUBRID/SQL Server 호환성 별도 검증 필요 (사용자에게 안내).

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

### 2-d-e. failure_surfaces 결정 (AskUserQuestion multiSelect)

```python
AskUserQuestion(questions=[
  {
    "question": "이 testbed 가 시연할 장애 패턴? (다중 선택 가능)",
    "header": "장애 패턴",
    "multiSelect": True,
    "options": [
      {"label": "db-lock-contention", "description": "DB row/table lock 경합 → 응답시간 + 에러율 폭증"},
      {"label": "external-api-timeout", "description": "외부 의존성 무응답 → cascade 5xx"},
      {"label": "db-cpu-throttle", "description": "DB CPU 제한 → 전 서비스 쿼리 지연"},
      {"label": "traffic-flood", "description": "동시 요청 폭증 → thread pool 포화"}
    ]
  }
])
```

default 는 4개 모두 선택 (= 기본 plopvape-shop 패턴). 부분 선택 시 그만큼만 시나리오 생성.

각 surface 의 기본 lock_table / external_container 등은 LLM 이 services + db.schemas 보고 자동 매핑 (services-author 가 이 매핑을 scenario_hints 로 반환).

### 2-d-f. 사용자 최종 승인 (AskUserQuestion)

deep interview 결과 종합 표시 후:

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
```

```python
AskUserQuestion(questions=[
  {
    "question": "위 spec 으로 services-author 진행?",
    "header": "최종 승인",
    "multiSelect": False,
    "options": [
      {"label": "진행 (Recommended)", "description": "PR push_mode=pr 로 자동 생성"},
      {"label": "수정", "description": "어느 단계 다시 인터뷰? 자유 입력"},
      {"label": "취소", "description": "인터뷰 중단, run 보존"}
    ]
  }
])
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

## 단계 (c): NMS 모니터링 — 자동 감지 후 사용자 confirm

NMS = Network Management System. SNMP v2c/v3 응답하는 장비 (라우터/스위치/방화벽/AP/UPS 등) 를 Polestar10 에서 폴링 모니터링. 환경에 따라 있을 수도 없을 수도 있으므로 **자동 감지 후 결과 따라 분기**.

### Step 1: 자동 감지 시도

타겟 서버 SSH 접속 가능 후 다음 순서로 스캔 (best-effort):

```bash
# 1. 타겟 서버의 default gateway IP 추출 (라우터일 가능성 높음)
GW=$(ssh "$TESTBED_USER@$TESTBED_HOST" 'ip route | awk "/^default/ {print \$3}"' | head -1)

# 2. 타겟 서버의 같은 subnet 추출
SUBNET=$(ssh "$TESTBED_USER@$TESTBED_HOST" \
  'ip -o -f inet addr show | awk "/scope global/ {print \$4}"' | head -1)
# 예: 192.168.200.109/24

# 3. (방법 A) gateway 에 SNMP probe (community public, sysDescr OID)
SNMP_RESULT=$(timeout 3 ssh "$TESTBED_USER@$TESTBED_HOST" \
  "snmpwalk -v 2c -c public -t 1 -r 0 $GW .1.3.6.1.2.1.1.1.0" 2>/dev/null)

# 4. (방법 B, more comprehensive — nmap 가 깔려있으면)
NMAP_RESULT=$(ssh "$TESTBED_USER@$TESTBED_HOST" \
  "command -v nmap >/dev/null && sudo nmap -sU -p 161 --open -oG - $SUBNET 2>/dev/null | grep '161/open'")

# 5. (방법 C) Polestar10 에 이미 등록된 NMS 자원 조회 — 재인식 후보
ALREADY_REGISTERED=$(curl -sS --cookie-jar "$JAR" \
  "$POLESTAR10_BASE_URL/api/nms/v1/resources?testbed=$TESTBED_NAME" \
  | jq -r '.data[].host')
```

### Step 2: 결과 분기

#### Case A: 1+ 장비 발견

```python
# 발견된 장비 리스트를 옵션으로 표시 (max 4개, 더 많으면 truncate + Other)
AskUserQuestion(questions=[
  {
    "question": "다음 SNMP 장비가 자동 감지됐습니다. NMS 자원으로 등록할까요?",
    "header": "NMS 등록",
    "multiSelect": True,
    "options": [
      {"label": "192.168.200.1 (가능: 라우터)", "description": "sysDescr: Cisco IOS XE 17.x — gateway"},
      {"label": "192.168.200.10 (가능: 스위치)", "description": "sysDescr: Juniper EX2300"},
      {"label": "192.168.200.20 (가능: 방화벽)", "description": "sysDescr: Palo Alto PA-220"},
      {"label": "다 등록 (Recommended)", "description": "발견된 장비 모두 NMS 자원으로 등록"}
    ]
  }
])
```

선택된 장비마다 추가 자유 입력 (community string, SNMP version) prompt.

#### Case B: 0 장비 발견 또는 스캔 실패 (snmpwalk/nmap 부재 또는 권한 없음)

```python
AskUserQuestion(questions=[
  {
    "question": "SNMP 장비가 자동 감지되지 않았습니다. NMS 등록을 어떻게 진행할까요?",
    "header": "NMS",
    "multiSelect": False,
    "options": [
      {"label": "Skip (Recommended)", "description": "이 환경에 SNMP 장비 없음. NMS 등록 안 함."},
      {"label": "직접 입력", "description": "사용자가 SNMP 장비 IP + community string + version 직접 입력"}
    ]
  }
])
```

`직접 입력` 시 자유 입력 prompt:
```
"장비 IP?" (예: 192.168.200.1)
"SNMP version (v2c/v3, default v2c)?"
"community string (default public)?"
```

#### Case C: 자동 감지 도구 부재 (snmpwalk + nmap 둘 다 없음)

타겟 서버에 추가 설치 권하지 않고 fallback:
```
"자동 감지 불가 — 타겟 서버에 snmpwalk/nmap 미설치. SNMP 장비가 있는지
 사용자께서 알고 계신가요? 있으면 IP 입력 (없으면 Enter)."
```

### interview.yaml 산출

```yaml
nms:
  enabled: true | false   # 발견 + 사용자 confirm 시 true
  detection_method: "snmpwalk" | "nmap" | "manual" | "none"
  devices:
    - host: "192.168.200.1"
      snmp_version: "v2c"
      community: "public"
      sysDescr: "Cisco IOS XE 17.x"
      role: "router"
```

### Phase 1-A 묶음과의 관계

이 단계는 Phase 1-A (배포 앱 + Polestar10 모드) **이후**에 별도로 실행. 자동 감지가 SSH 접속 가능 시점 (= target host 확정 후) 에만 가능하므로 묶음에 못 들어감.

순서:
1. Phase 1-A 묶음 (배포 앱 + P10 모드)
2. target host 자유 입력 (IP/user/password)
3. SSH ping 확인
4. **NMS 자동 감지** (이 섹션) → 결과 따라 인터뷰
5. Phase 1 완료 → architecture-draft

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

## 단계 (d): Polestar10 웹 조작 모드 — Phase 1-A 묶음에 포함됨

위 Phase 1-A 의 세 번째 질문 ("Polestar10 자원 등록 모드?") 으로 처리. 아래는 참고용 (옛 형식):

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

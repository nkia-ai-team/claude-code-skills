# 패턴 카드 → 인스턴스 스크립트 변환 룰

`scenario-patterns/<pattern>.md` 카드 + `service-spec.yaml` 메타 → 실제 실행 가능한 bash 스크립트.

---

## 변환 알고리즘

### 1. 카드 read
```
Read: <patterns_root>/<pattern>.md
```

### 2. 치환 슬롯 추출
카드의 `## 치환 슬롯` 섹션 마크다운 리스트에서 변수명 + 의미 추출.

예 (db-lock-contention.md):
- `LOCK_TABLE` — 도메인별 핫 row 가 있는 테이블
- `LOCK_KEY` — 그 row 의 식별자
- `LOAD_ENDPOINT` — 그 row 를 갱신하는 API
- `HOLD_SECS` — lock 점유 기간
- `LOAD_CONCURRENCY` — 동시 요청 수

### 3. service-spec.yaml 메타 + 사용자 인터뷰로 변수 채움

| 치환 슬롯 | 자동 결정 가능? | 자동 결정 룰 | 사용자 인터뷰 (자동 안 될 때) |
|---|---|---|---|
| `NAMESPACE` | O | service-spec.target.namespace | — |
| `SERVICE_API` | O | service-spec.target.api_base | — |
| `LOCK_TABLE` (db 패턴) | △ | 도메인이 e-commerce → `inventory`, banking → `accounts`, 예약 → `seats` | "어떤 테이블이 lock 점유 핫스팟?" |
| `LOCK_KEY` (db 패턴) | X | — | "lock 걸 row 의 식별자? (예: 'product-123')" |
| `LOAD_ENDPOINT` | △ | 패턴-도메인 룩업 (아래 표) | "부하 줄 endpoint?" |
| `LOAD_PAYLOAD` | △ | LOAD_ENDPOINT 의 도메인 모델 보고 LLM 추론 | "POST 바디 JSON?" |
| `HOLD_SECS`, `LOAD_DURATION_SEC` | O | estimated_duration_sec 의 50~80% | — |
| `LOAD_CONCURRENCY` | O | 패턴 default | — |
| `EXTERNAL_CONTAINER` (timeout 패턴) | △ | 도메인 추론 | "외부 의존성 컨테이너 이름?" |
| `DB_DEPLOYMENT`, `DB_CONTAINER` (cpu 패턴) | O | service-spec 의 db 종류 | — |

### 4. 패턴-도메인 룩업 표 (자동 추론 사전)

| 패턴 | 도메인 | LOCK_TABLE / LOAD_ENDPOINT / EXTERNAL 추론 |
|---|---|---|
| db-lock-contention | e-commerce | `inventory` / `/api/orders` / — |
| db-lock-contention | banking | `accounts` / `/api/transfer` / — |
| db-lock-contention | 예약 | `seats` / `/api/reservations` / — |
| external-api-timeout | e-commerce | — / `/api/orders` / `pg-mock` |
| external-api-timeout | banking | — / `/api/payment` / `external-pg-mock` |
| db-cpu-throttle | 모든 | — / `/api/<주력 endpoint>` / — |
| traffic-flood | 모든 | — / `/api/<진입 endpoint>` / — |

### 4-b. scenario_hints (신규 도메인 자동 생성 시)

새 testbed 생성 시 testbed-engineer 의 services-author 모드가 코드 생성 후 `scenario_hints` 를 manifest 에 보존:

```yaml
# manifest.yaml.scenario_hints (Phase 6 산출, Phase 10 입력)
scenario_hints:
  lock_table: "accounts"               # services-author 가 db.schemas 에서 핫 row 후보 추출
  lock_key_example: "account-1"        # seed 데이터 PK
  lock_endpoint: "/api/transfer"        # 그 row 갱신하는 endpoint
  lock_payload: {"from_account": "account-1", "to_account": "account-2", "amount": 100}
  external_endpoint: "/api/transfer"
  external_container: "external-pg-mock"  # docker-compose 가 외부 mock 운영 시
  primary_load_endpoint: "/api/transfer"  # traffic-flood 진입점
  db_deployment: "postgres"
  db_container: "postgres"
```

**우선순위**: scenario_hints 가 있으면 룩업 표 + 사용자 인터뷰 모두 우회. testbed-engineer 가 생성한 코드의 실제 schema 기반이라 정확.

### 4-c. 룩업 결정 알고리즘

```
1. scenario_hints 가 manifest 에 존재? → 그대로 사용 (신규 도메인)
2. interview.app.domain 이 룩업 표의 키? → 표 사용 (e-commerce / banking / 예약)
3. 그 외 → 사용자 인터뷰 fallback
```

테스트베드 generate-scenarios 단독 호출 (scenario_hints 없음, 룩업 표에도 없는 도메인):
```
사용자에게 prompt:
  "도메인 매핑 정보가 없습니다. 다음 변수를 직접 입력하시거나 LLM 추론에 위임:
   - LOCK_TABLE: _
   - LOAD_ENDPOINT: _
   - LOAD_PAYLOAD: _
   ...
   또는 'auto' 선택 시 testbed-services 레포의 코드 (controller / entity) 를 LLM 이 분석하여 추론."
```

`auto` 선택 시:
- LLM 이 `<TESTBED_SVC_REPO>/<testbed_name>/*-service/src/main/java/.../*Controller.java` Read
- `@PostMapping` / `@GetMapping` / `@RequestMapping` annotation 으로 endpoint 목록 추출
- `<TESTBED_SVC_REPO>/<testbed_name>/db/init.sql` 의 CREATE TABLE 로 테이블 추출
- 트랜잭션 도메인 (transfer, orders) endpoint + 핫 테이블 후보 자동 매핑
- 사용자 confirm 후 진행

### 5. 추론 충돌 시

자동 추론이 가능해 보여도 confidence 낮으면 사용자 인터뷰. 룰:
- service-spec.yaml 에 명시 X
- 도메인 명확하게 매핑 안 됨 (자유 입력 도메인 등)
- 같은 도메인에 여러 후보 (e-commerce 인데 `inventory` vs `cart` 둘 다 핫스팟)

→ "다음 변수들의 값이 필요합니다. 답변해주시거나 default 사용 [yes 일관 default]:"

---

## 인스턴스화 예시

### 예시 1: e-commerce 에 db-lock-contention 추가

입력:
- service-spec.yaml: `name=plopvape-shop`, `namespace=rca-testbed`, `api_base=http://127.0.0.1:30080`
- 도메인 추론: e-commerce
- 패턴: db-lock-contention
- 사용자: count=1, slug=`product-lock`

자동 결정:
- `LOCK_TABLE=inventory` (도메인 룩업)
- `LOAD_ENDPOINT=/api/orders` (도메인 룩업)
- `LOCK_KEY=product-1` (사용자 인터뷰: "어떤 row?")
- `HOLD_SECS=180` (estimated_duration_sec=300 의 60%)
- `LOAD_CONCURRENCY=30` (패턴 default)

산출 스크립트 (요지):
```bash
#!/bin/bash
# scenario-05-product-lock.sh
NAMESPACE="${NAMESPACE:-rca-testbed}"
SERVICE_API="${SERVICE_API:-http://127.0.0.1:30080}"
LOCK_TABLE="${LOCK_TABLE:-inventory}"
LOCK_KEY="${LOCK_KEY:-product-1}"
LOAD_ENDPOINT="${LOAD_ENDPOINT:-/api/orders}"
LOAD_PAYLOAD='{"product_id":"product-1","quantity":1}'
HOLD_SECS="${HOLD_SECS:-180}"
LOAD_CONCURRENCY="${LOAD_CONCURRENCY:-30}"
# ... 카드 골격 그대로
```

산출 yaml entry:
```yaml
- id: scenario-05
  file: scenario-05-product-lock.sh
  title: Product Inventory Row Lock
  description: inventory 테이블 product-1 row 에 long-held lock + 동시 주문
  root_cause: 장시간 SELECT FOR UPDATE lock 점유
  propagation: lock wait → /api/orders timeout → 502
  estimated_duration_sec: 300
  expected_alarms:
    - DPM lock wait
    - APM order 평균응답시간 초과
    - APM order 에러율 급증
```

### 예시 2: banking 에 external-api-timeout 추가

입력:
- service-spec.yaml: `name=core-banking`, `domain=banking` (yaml 에 metadata 없으면 사용자 인터뷰)
- 패턴: external-api-timeout
- 사용자: slug=`payment-pg-down`

자동 결정:
- `LOAD_ENDPOINT=/api/payment` (banking 룩업)
- `EXTERNAL_CONTAINER=external-pg-mock` (banking 룩업)
- `LOAD_PAYLOAD=...` (사용자 인터뷰 또는 LLM 추론)

---

## LLM 호출 위치 (이 스킬 안에서)

다음 단계만 LLM 추론 (나머지는 단순 substitution):

1. **자동 추론 (치환 슬롯 채우기)** — service-spec.yaml + 도메인 + 패턴 → 변수 값
2. **LOAD_PAYLOAD 합성** — endpoint 의미 보고 의미 있는 JSON 작성
3. **slug 작성** — 사용자 입력 없으면 패턴 + 도메인 + 변수로 짧은 slug 생성

이 추론은 인라인으로 처리 (오케스트레이터의 자체 컨텍스트). 무거운 코드 생성은 testbed-engineer agent 위임 가능하지만 Phase 1 에서는 인라인 충분.

---

## 변환 검증 체크리스트

스크립트 생성 후 사용자 미리보기 전에:

- [ ] `script-template.md` 의 필수 요소 모두 포함 (`trap cleanup EXIT`, `set -euo pipefail`, cleanup 모드 분기, `[OK] done`)
- [ ] `service-spec.yaml` 의 새 entry 가 기존 entry 와 같은 indent + 필드 순서
- [ ] `id` 가 unique (`scenario-<NN>` 의 NN 가 기존과 충돌 X)
- [ ] `script_filename` 이 실제 파일과 일치
- [ ] `expected_alarms` 가 빈 배열 X (적어도 1개)
- [ ] `estimated_duration_sec` 가 합리적 (60~600 범위)
- [ ] cleanup 이 멱등 (반복 호출 안전)
- [ ] 비밀 정보 (자격증명) 가 스크립트에 hardcode 안 됨

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
# manifest.yaml.scenario_hints (services_author 산출, generate_scenarios 입력)
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

### 4-c. 룩업 결정 알고리즘 — fallback 명확화 (강제 룰)

```
1. scenario_hints 가 manifest 에 존재? → 그대로 사용 (신규 도메인)
2. interview.app.domain 이 룩업 표의 키? → 표 사용 (e-commerce / banking / 예약)
3. 그 외 → auto 모드 강제 진입 (코드 분석)
4. auto 결과 confidence 낮으면 → 사용자 인터뷰
5. 사용자 인터뷰도 결정 안 되면 → fail-fast (시나리오 생성 중단)
```

🚫 **강제 금지 룰 — plopvape-shop 시나리오 sed 치환 절대 X**

새 testbed (food-delivery / banking / IoT / 사용자 정의 도메인 등) 의 시나리오 생성 시 plopvape-shop 의 `scripts/*.sh` 를 sed 치환으로 변환하는 shortcut **절대 금지**. 이유:

- plopvape 의 시나리오는 e-commerce 도메인 전용 (orders 테이블 / inventory.id / pg-mock 컨테이너 / NodePort 30080)
- 다른 도메인에 sed 치환 시 비즈니스 의미 X — orders 테이블 자체가 없는 testbed 에서 `SELECT * FROM orders FOR UPDATE` 실행하면 SQL error
- 변수 이름만 치환되고 SQL / endpoint / payload / 외부 의존성 컨테이너 모두 plopvape 가정 그대로 — 사용자가 보고서에서 직접 "비즈니스 도메인 정확성 검증 X" 라고 admit 한 패턴

신규 도메인 시나리오는 **반드시 auto 모드 (코드 분석) 또는 사용자 인터뷰** 거쳐 도메인-specific 합성. plopvape `.sh` 파일 read 후 변환 금지.

### 4-d. auto 모드 — 신규 도메인 코드 분석 강제 절차

룩업 표에 없는 도메인 (food-delivery / banking 새 변형 / IoT 등) = auto 모드 강제. LLM 이 다음 파일 read **필수**:

| read 대상 | 추출 정보 |
|---|---|
| `<TESTBED_SVC_REPO>/<testbed_name>/*-service/src/main/java/.../*Controller.java` | `@PostMapping` / `@GetMapping` / `@RequestMapping` 의 path + HTTP method + body schema |
| `<TESTBED_SVC_REPO>/<testbed_name>/db/init.sql` (또는 `db/schema.sql`) | `CREATE TABLE` 의 테이블명 + 컬럼 + PK/FK + seed data |
| `<TESTBED_SVC_REPO>/<testbed_name>/k8s/*.yaml` | NodePort 실제 port (30080 가정 X), Service 이름, 외부 의존성 컨테이너 (`pg-mock` / `external-pg-mock` 등 도메인별로 다름) |
| `<TESTBED_SVC_REPO>/<testbed_name>/docker-compose.dev.yml` (있다면) | 외부 mock 컨테이너 이름 정확히 확인 |

읽은 후 LLM 이 다음 매핑 합성 (도메인 추론):

| 패턴 | 매핑 후보 (LLM 추론) |
|---|---|
| db-lock-contention | 핫 테이블 = 트랜잭션 도메인의 PK 충돌 가능 테이블 (food-delivery 면 `orders` 또는 `restaurant_inventory`. banking 이면 `accounts`. IoT 면 `device_state`) |
| external-api-timeout | 외부 의존성 컨테이너 = k8s manifest 또는 docker-compose 에서 발견된 mock 이름 (`external-pg-mock` 그대로 가정 X) |
| db-cpu-throttle | DB Deployment / container 이름 = k8s manifest 의 실제 값 |
| traffic-flood | 진입 endpoint = Controller 의 `@PostMapping("/api/<도메인 트랜잭션>")` |

**confidence 낮은 경우** (Controller 가 너무 많아서 어떤 endpoint 가 핫 path 인지 모호 / 테이블이 여러 개라 어떤 게 lock 핫 row 인지 모호) → 사용자 인터뷰:
```
"food-delivery 의 db-lock-contention 시나리오에 사용할 변수를 결정해 주세요:
  - LOCK_TABLE 후보: orders / restaurant_inventory / order_items (init.sql 분석 결과)
  - LOAD_ENDPOINT 후보: POST /api/orders / POST /api/orders/cancel (Controller 분석 결과)
  - 도메인 의도: 어떤 트랜잭션 핫스팟을 시뮬레이션? _"
```

**confidence 높음** (단일 후보 명확) → 사용자에게 결정 사항 표시 후 confirm 받고 진행 (silent 진행 X — 사용자가 도메인 적합성 검증).

### 4-e. fail-fast — 신규 도메인인데 코드 분석 불가능한 경우

testbed-services 레포 자체에 testbed 디렉토리 없거나 controller / init.sql 부재 시:
- plopvape sed 치환으로 fallback X
- 사용자에게 명시: "코드 분석 불가능. testbed-services 의 <testbed_name>/src/main/java + db/init.sql 가 필요. PR 머지 후 재호출하거나 사용자가 시나리오 직접 작성."
- 시나리오 생성 자체 abort

### 4-f. 도메인 비즈니스 시나리오 narrative 강제 (강제 룰)

⚠️ **변수 치환 (LOCK_TABLE / LOAD_ENDPOINT 등) 만으론 부족.** service-spec.yaml 의 시나리오 메타 (`description` / `root_cause` / `propagation`) 와 bash 스크립트의 부하 트리거 logic 이 **도메인의 실제 비즈니스 사건** 을 반영해야 함. 그렇지 않으면 4 패턴 catalog 가 모든 testbed 에 동일한 추상적 시나리오로 인스턴스화 → testbed 간 시나리오 구분 불가.

#### 강제 절차

각 시나리오 생성 시 다음 3 단계 narrative 합성 후 service-spec.yaml entry 에 박기:

1. **business trigger** — 도메인의 실제 사용자 행동 또는 외부 사건 (시간대 / 트랜잭션 종류 / 이벤트). 추상적 "동시 부하" X.
   - food-delivery + db-lock: "저녁 식사 시간대 (18~21시) 동시 주문 폭주 → orders 테이블 핫 row lock"
   - banking + db-lock: "월급일 직후 동시 이체 → accounts 테이블 잔액 row lock"
   - e-commerce + db-lock: "프로모션 시작 직후 인기 상품 동시 결제 → inventory 핫 row lock"

2. **affected business flow** — 어느 사용자 흐름이 망가지는지. 단순히 "endpoint 응답 지연" X.
   - food-delivery: "주문 확정 실패 → 사용자 이탈 → 음식점 매출 손실"
   - banking: "이체 timeout → 사용자 재시도 → 중복 이체 위험"
   - e-commerce: "장바구니 결제 실패 → 카트 abandonment 증가"

3. **uniqueness check vs 기존 testbed** — 같은 패턴의 기존 testbed 시나리오 description 과 textually 다른지 검증.
   ```bash
   # 기존 testbed scenario 의 description 읽어 비교
   for tb in $(ls "$RUNNER_ROOT/scenarios/services/" | grep -v "^${TESTBED_NAME}$"); do
     yq ".scenarios[] | select(.pattern == \"$PATTERN\") | .description" \
       "$RUNNER_ROOT/scenarios/services/$tb/service-spec.yaml" 2>/dev/null
   done
   ```
   합성한 description 이 위 중 하나와 keyword 다수 (≥3) 겹치면 → **도메인 특색 약함**. business trigger 재합성 또는 사용자 인터뷰.

#### service-spec.yaml 시나리오 entry 필드 표준

```yaml
- id: scenario-01-orders-evening-lock
  file: scenario-01-orders-evening-lock.sh
  title: "저녁 식사 시간대 주문 폭주 → orders row lock"
  pattern: db-lock-contention
  description: |
    food-delivery 의 핵심 비즈니스 시점 (18~21시 저녁 식사 시간대) 에 동시 주문
    폭주가 발생하면 orders 테이블의 PK row 에 lock 경합 발생. checkout API 의
    응답 지연 + payment-service 의 timeout 전파.
  root_cause: |
    동일 주문 row (가장 인기있는 음식점의 특정 메뉴) 에 동시 UPDATE 가
    경합. PostgreSQL row-level lock 이 큐잉되어 트랜잭션 시간 폭증.
  propagation: |
    1. order-service: checkout 응답시간 p99 > 5s (정상 < 500ms)
    2. payment-service: order-service 호출 timeout → cascading fail
    3. dispatch-service: 주문 확정 안 되니 배달 할당 못함
    4. 사용자: 결제 실패 경험 → 이탈 → 음식점 매출 손실
  business_trigger: "저녁 식사 시간대 동시 주문 폭주 (시뮬레이션: 1000 TPS × 60sec)"
  estimated_duration_sec: 120
  expected_alarms:
    - "DPM Lock Wait Time 초과 — testbed-postgres-0"
    - "APM 평균응답시간 초과 — order-service"
    - "APM 평균응답시간 초과 — payment-service"
```

`description` / `root_cause` / `propagation` / `business_trigger` 4 필드는 도메인 narrative 필수. 4 패턴 모두 동일 적용.

#### 검증 게이트

orchestrator (또는 사용자) 가 합성 결과 검토 후 다음 확인:
- [ ] description 에 도메인 비즈니스 키워드 ≥3 (예: food-delivery 면 "주문 / 음식점 / 배달 / 결제" 중 3+)
- [ ] root_cause 가 단순히 "lock 경합" 이 아닌 "어떤 row / 어떤 시점 / 어떤 트랜잭션" 까지 명시
- [ ] propagation 이 사용자 영향까지 추적 (4 단계 이상)
- [ ] 기존 testbed 의 같은 패턴 description 과 textually 구분됨

위 4 항목 중 하나라도 미흡 → 재합성 또는 사용자 인터뷰.

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

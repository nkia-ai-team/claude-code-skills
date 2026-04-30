# Architecture v1 Markdown 템플릿

testbed-build Phase 3 에서 인라인으로 채워 사용자 승인 받는 문서.

## 변수 substitution

interview.yaml 의 답변으로 다음 변수 채움:
- `{{TESTBED_NAME}}` — interview.app.testbed_name
- `{{TARGET_HOST}}` — interview.target.host
- `{{TARGET_USER}}` — interview.target.user
- `{{TARGET_ARCH}}` — interview.target.arch
- `{{NAMESPACE}}` — interview.app.namespace
- `{{DB_KIND}}` — interview.app.db_kind
- `{{NMS_ENABLED}}` — interview.nms.enabled
- `{{P10_BASE_URL}}` — bootstrap.polestar10.base_url
- `{{REGISTRATION_MODE}}` — interview.polestar10.registration_mode
- `{{RUN_ID}}` — runs/<RUN_ID>
- `{{IS_NEW_VARIANT}}` — interview.app.is_new_variant (true 면 deep interview 산출)
- `{{DOMAIN}}` — interview.app.domain (자유 도메인 또는 카테고리 이름, 새 testbed 시)
- `{{SERVICES_TABLE}}` — interview.app.services[] 렌더링 (새 testbed) 또는 testbed-services 의 service-spec 추론 (기존)
- `{{DB_SCHEMAS_BLOCK}}` — interview.app.db.schemas[] 의 SQL DDL preview (새 testbed 시만)
- `{{FAILURE_SURFACES}}` — interview.app.failure_surfaces[] (4종)

## 템플릿

```markdown
# RCA 테스트베드 아키텍처 v1

**Run ID**: {{RUN_ID}}
**생성**: testbed-build orchestrator
**Linear**: NKIAAI-542

---

## 개요

| 항목 | 값 |
|---|---|
| 테스트베드 이름 | {{TESTBED_NAME}} |
| 도메인 | {{DOMAIN}} |
| 새 testbed? | {{IS_NEW_VARIANT}} {{#if IS_NEW_VARIANT}}— services-author 가 코드 자동 생성{{/if}} |
| 타겟 서버 | {{TARGET_HOST}} ({{TARGET_USER}}, {{TARGET_ARCH}}) |
| K8s namespace | {{NAMESPACE}} |
| DB 종류 | {{DB_KIND}} |
| NMS 모니터링 | {{NMS_ENABLED}} |
| Polestar10 endpoint | {{P10_BASE_URL}} |
| Polestar10 등록 모드 | {{REGISTRATION_MODE}} |
| failure surfaces | {{FAILURE_SURFACES}} |

## Services 분할

{{SERVICES_TABLE}}

<!--
새 testbed 시 (interview.app.services[] 렌더링):

| 서비스 | 책임 | endpoints | depends_on |
|---|---|---|---|
| account | 계좌 조회, 잔액 조회 | GET /api/accounts/{id}, GET /api/accounts/{id}/balance | — |
| transfer | 계좌 이체 실행 | POST /api/transfer | account |
| ledger | 거래 내역 | GET /api/ledger/{accountId} | transfer |
| audit | 감사 이벤트 | POST /api/audit/event | — |

기존 testbed (plopvape-shop) 시: testbed-services 레포의 service-spec 또는 디렉토리 스캔 결과 표시.
-->

{{#if IS_NEW_VARIANT}}
## DB 스키마 (자동 생성)

```sql
{{DB_SCHEMAS_BLOCK}}
```

<!--
interview.app.db.schemas[] 를 SQL DDL 로 렌더링.

CREATE TABLE accounts (
  id          VARCHAR(64) PRIMARY KEY,
  ...
);
-->
{{/if}}

---

## 토폴로지

```mermaid
graph TB
  subgraph "{{TARGET_HOST}} ({{TARGET_ARCH}})"
    K3s[K3s 클러스터]
    subgraph "Namespace: {{NAMESPACE}}"
      App[5 Microservices<br/>(order/product/inventory/payment/notification)]
      DB[({{DB_KIND}})]
    end
    K3s --> App
    K3s --> DB
  end

  subgraph "Polestar10 Agents"
    SMS[SMS<br/>호스트 monitoring]
    KCM[KCM<br/>K8s DaemonSet]
    APM[APM JVM agent]
    WPM[WPM JVM agent]
  end

  Host[{{TARGET_HOST}}] --> SMS
  K3s --> KCM
  App --> APM
  App --> WPM

  subgraph "Polestar10 Backend ({{P10_BASE_URL}})"
    DPM[DPM]
    NMSagent[NMS]
    Collector[Collector]
  end

  DPM -.DB 직접접속.-> DB
  SMS -.heartbeat.-> Collector
  KCM -.metrics.-> Collector
  APM -.OTLP.-> Collector
  WPM -.UDP/TCP.-> Collector
```

---

## 6종 Polestar10 자원 등록 계획

| 에이전트 | 호스트 설치? | 등록 자원 (예상) | 비고 |
|---|---|---|---|
| SMS | ✅ systemd | 호스트 1개 ({{TARGET_HOST}}) | qemu-user-static (ARM 시) |
| KCM | ✅ DaemonSet | 클러스터 1개 | ARM 은 lucida-kcmagent 소스 빌드 |
| APM | ✅ JVM agent | 5 services | OTLP collector |
| WPM | ✅ JVM agent | 5 services | UDP/TCP collector |
| DPM | ❌ (DB-direct) | 1 자원 ({{DB_KIND}}@{{NAMESPACE}}) | Polestar10 backend 직접 접속 |
| NMS | ❌ (SNMP polling) | {{#if NMS_ENABLED}}<장비 N개>{{else}}skip{{/if}} | SNMP v2c/v3 |

---

## 알람 정책 (Phase 10 후 채워짐)

> 본 단계에서는 placeholder. Phase 10 (testbed-tune-alarms) 완료 후 자동 재작성됨.

---

## 시나리오 (Phase 9 후 채워짐)

> 본 단계에서는 placeholder. Phase 9 (testbed-generate-scenarios) 완료 후 자동 재작성됨.

---

## 사용 phase 목록 (오케스트레이터 흐름)

| Phase | 작업 | 주요 컴포넌트 |
|---|---|---|
| 1 | 인터뷰 4단계 (+ 새 testbed 시 deep interview) | 인라인 |
| 2 | Polestar10 연결 사전 체크 | curl preLogin |
| 3 | 아키텍처 v1 작성 | 인라인 (이 문서) |
| 4 | 사용자 승인 ⛔ | — |
| 5 | Concurrency lock | flock |
| 6 | Services-author (새 testbed 시만) | testbed-engineer agent — testbed-services 레포에 코드 생성 + git push |
| 7 | Dynamic inventory 생성 | 인라인 |
| 8 | ansible-playbook 실행 | site.yml + 7 roles (common / agent-wpm / agent-apm / service-k8s / agent-kcm / agent-sms / scenario-runner) |
| 9 | Polestar10 자원 등록 | testbed-polestar10-register |
| 10 | 시나리오 생성 | testbed-generate-scenarios (scenario_hints 활용) |
| 11 | 알람 정책 합성 + 등록 | testbed-tune-alarms |
| 12 | Closed-loop verify (max 3) | testbed-verifier agent + tune-alarms 재호출 |
| 13 | Finalize 보고서 | 인라인 |
| 14 | Cleanup | runs 디렉토리 + lock release |

---

## 한계 + 주의사항

- **services-author 가 생성한 코드는 빌드 검증 (mvnw clean package) 까지만 자동**. 비즈니스 로직 자체의 정확성은 사람이 PR review 단계에서 확인 권장.
- **rca-scenario-runner refactor 가 머지 전이면** 시나리오는 yaml 만 떨어뜨리고 컨테이너 재시작 시점부터 활성화.
- **closed-loop max retry = 3**. 실패 시 PARTIAL/FAIL 결과로 finalize. 수동 분석 필요할 수 있음.
- **단일 target 동시 실행 X**. flock 으로 가드.
- **새 testbed 시 PR 머지 대기**: push_mode=pr 면 PR 생성 후 사람이 머지해야 Phase 8 ansible 진행. push_mode=direct-push 시 자동.

---

이 아키텍처대로 진행하시겠습니까?

(승인 → Phase 5 lock 획득 → ansible 배포 시작. 25~45분 소요 예상.)
```

---

## 동적 부분 — Phase 9, 10 후 재작성

[Phase 9] testbed-generate-scenarios 완료 후 architecture.md 의 "## 시나리오" 섹션을 다음으로 교체:

```markdown
## 시나리오

| ID | 이름 | estimated_duration | expected_alarms |
|---|---|---|---|
| 01 | <name> | <sec>s | <count> 종 |
| ... |
```

[Phase 10] testbed-tune-alarms 완료 후 "## 알람 정책" 섹션 교체:

```markdown
## 알람 정책

총 <N> 개 정책 등록 / <M> 개 개별 알람.

### 공통 정책
| 이름 | 도메인 | 자원 적용 |
|---|---|---|
| ... |

### 개별 알람 (주요)
| 자원 | measurement | LEVEL2 | LEVEL3 | LEVEL4 |
|---|---|---|---|---|
| ... |
```

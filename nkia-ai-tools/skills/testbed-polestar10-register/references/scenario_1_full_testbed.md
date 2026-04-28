# Scenario 1 — 신규 테스트베드 구축

> "테스트베드 자원 한 번에 다 등록해줘"
> "RCA 테스트베드 셋업해줘"

여러 자원을 **하나의 서비스 그룹** 으로 묶어 일괄 등록. 가장 흔한 첫 사용 흐름.

---

## Trigger 키워드

`테스트베드`, `한 번에`, `일괄`, `다`, `구축`, `셋업`, `setup`

---

## Pre-conditions

- Bootstrap 완료 ([bootstrap.md](bootstrap.md))
- 모델별 추가 조건:
  - **agent-standby (서버/KCM/APM)**: 에이전트가 polestar10-itg collector 로 heartbeat 중. `READY` 가 standby 에 떠야 등록 가능
  - **DB-direct (DPM)**: polestar10 → DB 네트워크 도달 가능 (port reachable)
  - **SNMP-polling (NMS)**: polestar10 → 장비 SNMP UDP 161 도달 가능

---

## 등록 모델 분류 (5종)

리소스마다 등록 흐름이 다름. 시나리오 1 의 dispatch 는 type → 모델 매핑부터:

| 모델 | 적용 type | recipe | register endpoint | staging 방식 |
|---|---|---|---|---|
| **config-only** | Web URL, SLO | `add-target.md`, `slo.md` | `<type>/save` → `<type>/register` | 사용자가 명시적 save |
| **agent-standby** | 서버 (SMS), KCM | `add-target.md` | `<type>/standby-*/register` | 에이전트 heartbeat 자동 |
| **DB-direct** | DB (PG/Oracle/MySQL/MariaDB/SQLServer/Cubrid/Tibero) | `dpm-lifecycle.md` | `dpm/preregister` → `dpm/register` | 사용자 입력 폼 (host/port/db/user/pass) |
| **SNMP-polling** | NMS 네트워크 | `nms-lifecycle.md` | `nms/v1/pre/addResource` → `nms/v1/addResource` | 사용자 입력 폼 (IP/community/version) |
| **APM service-agent** | APM, WPM | `add-target.md` "APM Step 1/2" | `apm/standby-agent/register` (array) | service 단위 묶음, agent 단위 array register |

---

## Type 별 인터뷰 슬롯 (모델별 추가 입력)

공통 슬롯 (시스템 그룹 / 서비스 그룹 / 이상감지 정책) 외에 type 별로 추가로 받아야 할 정보:

| 모델 | 추가 슬롯 |
|---|---|
| config-only Web URL | name, url, method (GET/POST), connect/socket timeout, sslVerify |
| config-only SLO | name, sloTarget (%), evaluationCycle (DAILY/WEEKLY/MONTHLY), startDate, sliConditions[] |
| agent-standby (서버/KCM) | (없음 — standby 응답에서 자동) |
| DB-direct (DPM) | DB type, hostName, port, dbName, userName, password (+ ssl, topSQLCount 등 옵션) |
| SNMP-polling (NMS) | IP, port (default 161), SNMP version (v2c/v3), community (v2c) 또는 user/auth/priv (v3) |
| APM | (없음 — standby 응답에서 자동. service 단위 등록 묶음만 사용자 확인) |

---

## Dispatch flow

```
1. 인터뷰 — 테스트베드 메타 (공통)
   - 테스트베드 이름 (= 서비스 그룹 값. 기본: "RCA-Testbed")
   - 시스템 그룹 (기본: 1=Default. recipes/list-groups.md 응답에서 선택)
   - 이상감지 정책 (기본: "성능 이상감지 기본 정책")
   - 등록할 리소스 목록 + 각 리소스의 type

2. 서비스 그룹 사전 생성 (선택)
   recipes/service-group-tag.md  ← /api/cm/tag/value/insert
   ※ 등록 단계에서 자동 생성도 가능. 사전 insert 는 UI dropdown 노출용.

3. 리소스별 등록 — 모델 분류 → 각 모델로 라우팅

   [config-only — Web URL]
     a. recipes/add-target.md "Web URL 등록" Step 1  ← /api/weburl/save
     b. 응답의 data.id 추출
     c. Step 2  ← /api/weburl/register

   [config-only — SLO]
     a. recipes/slo.md Step 1  ← /api/cm/slo/register/standby
     b. recipes/slo.md Step 2  ← /api/cm/slo/list-filter (registered:false) 에서 SLO_ID 추출
     c. recipes/slo.md Step 3  ← /api/cm/slo/register

   [agent-standby — 서버 (SMS)]
     a. recipes/list-targets.md "Standby 조회" → /api/sms/standby-hosts-filter-step1
        hostStatus:"READY" 인 agentId 추출
        안 보이면 사용자에게 "에이전트 heartbeat 대기 (5~10분)" 안내 후 retry/skip
     b. recipes/add-target.md "서버 등록" Step 2 → /api/sms/standby-hosts/register
        payload 의 serviceGroupTagValue / groupId / anomalyPolicyTagValue 에 인터뷰 슬롯 주입

   [agent-standby — KCM]
     a. recipes/add-target.md "KCM Step 1" → /api/kcm/standby-clusters-filter-step1
        registeredStatus:"READY" 인 clusterId 추출
        안 보이면 KCM 에이전트 (cluster-installed) heartbeat 대기 안내
     b. recipes/add-target.md "KCM Step 2" → /api/kcm/standby-clusters/register

   [DB-direct — DPM]
     a. recipes/dpm-lifecycle.md "지원 DB" → /api/dpm/preregister/dbtypes
        응답 배열을 사용자에게 dropdown 으로 표시 (PostgreSQL/Oracle/MySQL/...)
     b. 인터뷰 (모델별 슬롯 표 참조): hostName, port, dbName, userName, password
     c. recipes/dpm-lifecycle.md "Step 1" → /api/dpm/preregister
        ⚠️ polestar10 가 직접 DB 접속 검증. 실패 시:
            - 자격증명 잘못 → 재입력 prompt
            - 네트워크 불통 → 방화벽/포트 확인 안내 후 skip
     d. recipes/dpm-lifecycle.md "Step 2" → /api/dpm/preregister/list 에서 resourceId 추출
     e. recipes/dpm-lifecycle.md "Step 3" → /api/dpm/register (resourceId 명시)

   [SNMP-polling — NMS]
     a. 인터뷰: IP, port (default 161), SNMP version, community (v2c)
     b. recipes/nms-lifecycle.md "Step 1" → /api/nms/v1/pre/addResource
        polestar10 가 SNMP 쿼리로 검증. 실패 시:
            - community/version 불일치 → 재입력 prompt
            - SNMP 응답 없음 → 장비 SNMP 활성화 / UDP 161 도달성 확인 안내
     c. recipes/nms-lifecycle.md "Step 2" → /api/nms/v1/pre/list 에서
        resourceId / systemName / description 자동 추출 (SNMP 응답으로 채워짐)
     d. recipes/nms-lifecycle.md "Step 3" → /api/nms/v1/addResource
        ⚠️ collectType 필드의 대소문자 비일관 함정 — recipe 본문이 안전하게 처리

   [APM — service+agent 2-level]
     a. recipes/add-target.md "APM Step 1" → /api/apm/standby-agents-filter-step1
        같은 serviceName 의 agent 들 묶음 표시
     b. 사용자에게 등록할 service 선택 (한 번에 올릴 service 1개~N개)
     c. recipes/add-target.md "APM Step 2" → /api/apm/standby-agent/register
        해당 service 의 모든 agent 를 array body 로 일괄 등록
        category 필드 ("APM" 또는 "WPM") 는 standby 응답 그대로 복사

   [TBD — Syslog/SQL/SNMP OID/사용자정의]
     UI fallback 안내 (recipes/add-target.md "UI Fallback") + 등록 후 list-filter 로 검증

4. 일괄 검증
   recipes/list-targets.md 의 type 별 list-filter 로 새 자원 모두 보이는지 확인
   /api/cm/portal/configuration/count 전체 수 증가 확인
   DPM 은 type 별 /api/dpm/<dbtype>/list, NMS 는 /api/nms/v1/list,
   APM/KCM 도 각각 별도 list endpoint

5. 보고
   - 등록 성공/실패 자원 (모델별로 묶어서 표시)
   - 사용한 서비스 그룹 / 시스템 그룹 / 이상감지 정책
   - 다음 단계 안내 (개별 알람 = 시나리오 2, 삭제 = 시나리오 4)
```

---

## 멱등성 (모델별 사전 체크)

| 자원 종류 | 사전 체크 | 충돌 시 처리 |
|---|---|---|
| Web URL | `weburl/list-filter` 의 `resourceName` 매칭 | skip / 사용자 prompt |
| 서버 | `sms/hosts-filter` 의 `hostname` 매칭 | 이미 MANAGED 면 skip |
| KCM | `kcm/standby-clusters-filter-step1` 의 `clusterId` 매칭 | 이미 등록됐으면 skip |
| DPM | `dpm/<dbtype>/list` 에서 `host:port:dbName` 조합 매칭 | 이미 있으면 prompt (재등록 = unregister + register, 알람 reattach) |
| NMS | `nms/v1/list` 의 `ipAddress` 매칭 | skip |
| APM | `apm` list 의 `serviceName` 매칭 | service 자체 이미 있으면 skip; agent 만 추가면 standby 에서 새 agent 만 register |
| SLO | `cm/slo/list-filter` 의 `name` 매칭 (registered:true/false 양쪽) | skip 또는 staging 정리 후 재등록 |
| 서비스 그룹 | `cm/tag/value/insert` 자체가 멱등 | 별도 처리 불필요 |

---

## 실패 시 부분 롤백

리소스 N개 중 일부 실패한 경우:
- 자동 롤백은 하지 않음 (의도치 않은 삭제 위험)
- 사용자에게 "이미 등록된 N개 + 실패 1개 + 미시도 M개" 상태 표 제시
- 다음 옵션:
  - 시나리오 4 (resource cleanup) 으로 부분 정리
  - 실패 항목만 retry
  - 그대로 두고 UI 에서 마저 진행

---

## 사용자에게 보여줄 최종 요약 예 (확장)

```
RCA 테스트베드 등록 완료
   서비스 그룹: RCA-Testbed (자동 생성)
   시스템 그룹: Default (id=1)
   이상감지 정책: 성능 이상감지 기본 정책

   서버 (3): plopvape-app, plopvape-db, dgx-spark
   DB (1):  plopvape (PostgreSQL @ db-host:30432)
   APM (1): plopvape-shop (3 agents: inventory, order, payment)
   KCM (1): plopvape-cluster
   NMS (1): core-switch (192.168.x.y, SNMPv2c)
   Web URL (1): plopvape-shop probe
   SLO (1): testbed-availability-weekly

   다음 단계 추천:
     • 개별 알람 추가:    시나리오 2 — "<자원>에 알람 걸어줘"
     • 자원 정리:          시나리오 4 — "<자원> 삭제"
```

# polestar10 엔드포인트 스펙

DevTools HAR 캡처 + curl 검증으로 확인한 polestar10 내부 API 명세.

- **Base URL**: `$POLESTAR10_BASE_URL` 환경변수, 미지정 시 `https://192.168.230.104` (NKIA team dev). self-signed 인증서 → curl `-k`
- **인증**: 쿠키 세션 (`accessToken`/`refreshToken` JWT). **CSRF 헤더 없음**
- **Content-Type**: `application/json`
- **응답 포맷**: `{success, data, errorCode, errorMsgArgs, errorData}`

실제 실행 가능한 bash + curl 레시피는 [`recipes/`](./recipes/).

---

## 공통 — 세션 / 인증

| 항목 | 값 |
|---|---|
| 로그인 단계 | 3-step challenge-response |
| 세션 쿠키 | `accessToken` (HttpOnly, SameSite=None, Secure), `refreshToken` |
| CSRF | 없음 |
| MFA | 사용자별. 비활성 시 3-step, 활성 시 TOTP 경로 |
| 비밀번호 해싱 | `sha512(plaintext).hex` (소문자 hex, 128자) |
| challengeResponse | `sha512(sha512(plaintext).hex + challenge).hex` |
| 세션 만료 | accessToken 1h, refreshToken ~24h |

→ [`recipes/login.md`](./recipes/login.md)

---

## 관리대상 등록 모델

polestar10 의 관리대상 등록 모델은 **3 가지** (검증 완료):

| 모델 | 적용 type | staging 진입 | register | 식별자 필드 (register body) |
|---|---|---|---|---|
| **Config-only** | Web URL, SLO, Syslog, SQL, SNMP OID, 연계 시스템 등 | `POST /api/<type>/save` (사용자 UI 폼) | `POST /api/<type>/register` (array body) | `id` (save 응답의 mongo id) |
| **Agent-based** | 서버 (SMS), APM, KCM, NMS | 에이전트 heartbeat 자동 → standby 자동 출현 | `POST /api/<service>/standby-*/register` (array body) | `agentId` (에이전트 자체 ID) |
| **DB-direct** | DPM (postgresql/oracle/mysql/mariadb/sqlserver/cubrid/tibero) | `POST /api/dpm/preregister` (DB 접속 정보 입력 + 검증) | `POST /api/dpm/register` (단일 객체 body) | `resourceId` (numeric 문자열, polestar10 자동 부여) |

**delete 패턴도 모델 별로 다름**:
- Config-only / Agent-based: `POST /api/<service>/<entity>/delete` body `{parameter:[...]}`
- **DPM**: **`GET /api/dpm/unregister/<resourceId>`** (GET method, body 없음)

**식별자 (delete body / 알람 confId) 형식 — type 별 표**:

| Type | resourceId / 식별자 | 알람 confId |
|---|---|---|
| weburl | save 응답 `data.id` 또는 list 응답 `id` (이미 prefix 됨) | `weburl_<24-hex-id>` |
| server.Server (SMS) | `MA_<hostname>_<timestamp>` | `<resourceId>_server.Server` |
| postgresql.PostgreSQL (DPM 인스턴스) | numeric 문자열 (예 `"954854831"`) | `<resourceId>_postgresql.PostgreSQL` |
| postgresql.Database (DPM 알람 대상) | (resource 자체는 없음, 알람용) | `<resourceId>_postgresql.Database_<dbName>` |
| apm.Agent | numeric 문자열 (음수 가능) | `<resourceId>_apm.Agent` |
| kcm.Cluster | `cluster-<uuid>` | (사용 X — Pod 단위 알람) |
| kcm.Pod | UUID (단순 — prefix 없음) | `<pod-uuid>` |
| nms (NMS) | 24-hex Mongo ID | (TBD) |
| log (custom monitor) | `MA_<...>_server.LogMonitor_<idx>` (= `customMonitorConfId`) | (TBD) |

---

## 확정된 엔드포인트 일람

### 인증
| Method | URL | 비고 |
|---|---|---|
| POST | `/api/account/pre-login` | step 1 |
| POST | `/api/cm/two-factor-authentication/enable` | step 2 (MFA 체크) |
| POST | `/api/account/login` | step 3 |
| POST | `/api/account/logout` | 세션 해제 |
| POST | `/api/account/token/valid` | 토큰 유효성 |

### 그룹 / 태그 (분류 체계)
| Method | URL | 용도 |
|---|---|---|
| POST | `/api/cm/groups/list` | **시스템** 그룹 목록 (Default=1, Root=0) — fixed |
| POST | `/api/cm/groups/tree` | 시스템 그룹 트리 |
| POST | `/api/cm/groups/children-with-configurations` | 그룹 + 소속 리소스 |
| POST | `/api/cm/tag/key/list` | tag 스키마 (CUSTOM/SYSTEM key 일람) |
| POST | `/api/cm/tag/value/insert` | **서비스 그룹** 등 CUSTOM tag value 추가 |
| POST | `/api/cm/tag/link/delete/value` | tag value 삭제 (path 비대칭) |
| POST | `/api/cm/tag/value` | (변형, 미확정) |
| POST | `/api/cm/tag/resource/select/<resourceId>` | 특정 리소스의 tag 들 조회 |

→ [`recipes/list-groups.md`](./recipes/list-groups.md), [`recipes/service-group-tag.md`](./recipes/service-group-tag.md)

### 카운트 (집계)
| Method | URL | body | 용도 |
|---|---|---|---|
| POST | `/api/cm/portal/configuration/count` | `{}` | 전체 관리대상 수 |
| POST | `/api/weburl/count` | `{}` | Web URL 수 |
| POST | `/api/sms/standby-hosts/count` | `{"parameter":"READY"}` | 서버 standby 수 (status 별) |
| POST | `/api/sms/standby-hosts/new/count` | `{"pageNumber":1,"pagePerSize":100,"sortFieldSets":[]}` | 신규 standby 수 |
| POST | `/api/apm/standby-agent/count` / `.../new/count` | (TBD) | APM standby |

### Web URL (config-only) — 풀 라이프사이클
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/weburl/save` | `{name, url, method, ...}` | `{data:{id, ..., registered:false}}` |
| POST | `/api/weburl/register` | `[{id, dataPolicy, tag, anomalyPolicyTagValue, groupId}]` (**array**) | `{data:null}` |
| POST | `/api/weburl/list-filter` | `{pageNumber:1, pagePerSize:30, gridFilters:[], sortFieldSets:[], tagFilters:["confType = weburl"]}` | `{data:{content:[{id:"weburl_..", resourceName, totalTimeMs, ...}], totalElements}}` |
| POST | `/api/weburl/detail` | `{parameter:"weburl_<id>"}` | `{data:{... 31개 필드 ...}}` |
| POST | `/api/weburl/delete` | `{parameter:["weburl_<id>", ...]}` | `{data:"ok"}` |
| POST | `/api/weburl/major-info` | (body 형태 미확정) | (TBD) |

→ [`recipes/add-target.md`](./recipes/add-target.md), [`recipes/delete-target.md`](./recipes/delete-target.md), [`recipes/list-targets.md`](./recipes/list-targets.md)

### 서버 (agent-based) — 풀 라이프사이클
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/sms/standby-hosts-filter-step1` | `{pageNumber:1, pagePerSize:30, gridFilters:[], sortFieldSets:[], arguments:{}}` | `{data:{content:[{agentId:"MA_..", hostname, ipAddress, hostStatus:"READY", ...}]}}` |
| POST | `/api/sms/standby-hosts-filter-step2` | `{pageNumber:1, pagePerSize:1000, arguments:{agentId:["MA_.."]}}` | step1 + 추가 상세 |
| POST | `/api/sms/standby-hosts/register` | `[{agentId, managementStatus:"MANAGED", collectorPolicyTagValue, serviceGroupTagValue, anomalyPolicyTagValue, groupId}]` | `{data:{failedCount, successCount}}` |
| POST | `/api/sms/hosts-filter` | `{pageNumber:1, pagePerSize:30, gridFilters:[], sortFieldSets:[], tagFilters:["confType = server"], arguments:{}}` | `{data:{content:[{resourceId:"MA_..", hostname, ip, cpuUtil, memUtil, managementStatus, ...}]}}` |
| POST | `/api/sms/hosts/delete` | `{parameter:["MA_.."]}` (agent ID 그대로, prefix 없음) | `{data:"ok"}` |

→ [`recipes/add-target.md`](./recipes/add-target.md), [`recipes/delete-target.md`](./recipes/delete-target.md), [`recipes/list-targets.md`](./recipes/list-targets.md)

> ⚠️ **주의**: 서버 삭제 후에도 SMS 에이전트가 살아있으면 다음 heartbeat 사이클에 자동 재출현 standby. 영구 제거하려면 **에이전트도 stop**.

### KCM (Kubernetes Cluster Monitoring) — agent-based, cluster 단위
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/kcm/clusters/list-filter` | `{pageNumber, pagePerSize, sortFieldSets, gridFilters, tagFilters:["confType = kcm"]}` | 등록된 cluster list |
| POST | `/api/kcm/standby-clusters-filter-step1` | `{pageNumber, gridFilters:[], sortFieldSets:[], pagePerSize:30}` | standby cluster list (`clusterId`, `clusterName`, `clusterVersion`, `agentVersion`) |
| POST | `/api/kcm/standby-clusters/count` | `{}` | standby 개수 |
| POST | `/api/kcm/standby-clusters/register` | `[{clusterId, managementStatus:"MANAGED", collectorPolicyTagValue, serviceGroupTagValue, anomalyPolicyTagValue, groupId}]` | 등록. 응답에 `registrationSucceedClusters` / `registrationFailedClusters` |
| POST | `/api/kcm/standby-clusters/unregister` | `{clusterId:"..."}` (단일 객체) | unregister |
| POST | `/api/kcm/measurement/definitions/resourcetype/<type>/metric` | `{}` | KCM 전용 메트릭 |
| POST | `/api/kcm/resource-explore/cluster/<id>/pods/list-filter` | `{...}` | 클러스터 내 Pod list |
| POST | `/api/kcm/resource-explore/cluster/<id>/status` | `{}` | 클러스터 상태 |

### APM (Application Performance Monitoring) — agent-based, service+agent 2-level
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/apm/services/list-filter` | `{pageNumber, pagePerSize, sortFieldSets:[{fieldName:"serviceName"}], tagFilters:[], startTime, endTime, gridFilters:[]}` | service list (`serviceId`, `serviceName`, `agentCount`, `category:"APM"|"WPM"`) |
| POST | `/api/apm/standby-agents-filter-step1` | `{pageNumber, gridFilters:[], sortFieldSets:[], pagePerSize:30, arguments:{}}` | standby agent list (`serviceName`, `agentId`, `resourceId`, `confId`, `category`) |
| POST | `/api/apm/standby-agent/count` / `/api/apm/standby-agent/new/count` | `{}` | standby 개수 |
| POST | `/api/apm/standby-agent/register` | `[{serviceName, agentId, resourceId, category, managementStatus, collectorPolicyTagValue, anomalyPolicyTagValue, serviceGroupTagValue, groupId}, ...]` | agent 단위 일괄 등록 |
| POST | `/api/apm/unregisterservice` | `[{serviceId, category}]` (array) | **service 단위 unregister — 그 service 의 모든 agent 함께 제거** |

> APM 의 특이점: **register 는 agent 단위 array, unregister 는 service 단위**. URL 명명도 일관성 없음 (`standby-agent/register` 단수 vs `unregisterservice` 한 단어).

### NMS (Network Monitoring System) — SNMP-polling 모델 (heartbeat 없음)
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/nms/v1/list` | `{pageNumber, pagePerSize, sortFieldSets, tagFilters:["confType = network"], gridFilters, timeFilter:{mode:"LIVE",...}, arguments:null}` | 등록된 NMS network list |
| POST | `/api/nms/v1/pre/list` | `{pageNumber, gridFilters:[], sortFieldSets:[], pagePerSize:30}` | pre-list staging (`pre/addResource` 호출 후 채워짐) |
| POST | `/api/nms/v1/pre/addResource` | `{collectType:"snmp", snmpVersion, host, port, community, ...}` | **SNMP 검증 staging** — polestar10 가 SNMP 쿼리로 systemName/description 채움 |
| POST | `/api/nms/v1/addResource` | pre 결과 + `{systemName, description, resourceId, resourceType:"network.Network", groupId, serviceGroupTagValue, anomalyPolicyTagValue, ...}` | 정식 등록 |
| POST | `/api/nms/v1/deleteResource/<resourceId>` | (none, path 에 ID) | 삭제 (POST + body 없음) |
| POST | `/api/nms/v1/measurement/definitions/resourcetype/<type>/metric` | `{}` | NMS 전용 메트릭 (`network.Network`/`network.Cpus`/`network.Memorys`/`network.Interface` 등) |
| POST | `/api/nms/v1/system/<id>` | `{}` | 시스템 상세 |
| POST | `/api/nms/v1/system/interface/<id>` | `{}` | 인터페이스 list |

> **NMS 등록 모델**: agent heartbeat 가 없음 (SNMP polling). DPM 과 비슷한 **사용자 입력 모델**:
> - Step 1: `pre/addResource` 로 SNMP 검증 (polestar10 가 장비에 SNMP 쿼리)
> - Step 2: `pre/list` 로 staging 의 resourceId/systemName 추출
> - Step 3: `addResource` 로 정식 등록
> - 명명 비일관성: pre 의 `collectType:"snmp"` (소문자) ↔ addResource 의 `"SNMP"` (대문자)

→ [`recipes/nms-lifecycle.md`](./recipes/nms-lifecycle.md)

### DPM (DB Performance Monitoring) — 별도 패턴
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/dpm/<dbtype>/list` | `{pageNumber, pagePerSize, sortFieldSets, gridFilters, tagFilters:["confType = <dbtype>"]}` | type 별 (postgresql/oracle/mysql/mariadb/sqlserver/cubrid/tibero) DB list |
| POST | `/api/dpm/preregister/dbtypes` | `{}` | 사용 가능 DB 타입 dropdown |
| POST | `/api/dpm/preregister` | DB 접속 정보 + 정책 + 그룹 (`{resourceType, hostName, port, dbName, userName, passwd, ...}`) | staging 입력 + DB 접속 검증 |
| GET | `/api/dpm/preregister/list` | (none) | staging 항목 list (resourceId 추출용) |
| POST | `/api/dpm/preregister/error-count` | `{parameter:"ERROR"}` | error 카운트 |
| POST | `/api/dpm/register` | preregister body + `resourceId` + `managementStatus:"MANAGED"` | **단일 호출 활성화** |
| **GET** | **`/api/dpm/unregister/<resourceId>`** | (none, path 에 ID) | **GET method** + body 없음 — 다른 type 과 다름 |
| POST | `/api/dpm/measurement/definitions/resourcetype/<type>/metric` | `{}` | DPM 전용 메트릭 catalog |
| POST | `/api/dpm/configuration/<id>/basic-info` | `{}` | config 정보 |
| GET | `/api/dpm/postgresql/instance/<id>/summary` | (none) | 인스턴스 summary |
| GET | `/api/dpm/postgresql/instance/<id>/efficiency` | (none) | 효율성 메트릭 |

> **DPM 등록 모델**: agent heartbeat 모델이 아니라 polestar10 가 DB 에 직접 접속해서 SQL 쿼리. 사용자가 등록 시점에 DB 접속 정보 입력 필요. 따라서 staging step (`save`) 없이 **`preregister` (DB 접속 검증) → `register` (활성화)** 흐름.

> **알람 cascade rule (검증 완료 — Phase B)**: DPM `unregister` 후 알람 정의는 **삭제되지 않고 orphan 으로 남음**. 같은 `resourceId` 로 재등록하면 알람 자동 reattach. 다른 resourceId 로 등록 시 알람은 영구 orphan.

→ [`recipes/dpm-lifecycle.md`](./recipes/dpm-lifecycle.md)

### SLO (config-only, 2-step 변형)
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/cm/slo/register/standby` | `{name, targetTags:["serviceGroup = ..."], setting:{sloTarget, evaluationCycle, startDate, weightFormula, excludeMaintenance}, sliConditions:[{type:"AVAILABILITY", rowKey:"A"}], ...}` | `{data:"ok"}` (id 안 반환) |
| POST | `/api/cm/slo/list-filter` | `{pageNumber:1, sortFieldSets:[], gridFilters:[{field:"registered", operator:"Equals", values:[true|false]}]}` | `{data:{content:[{id, name, sli, target, evaluationCycle, ...}]}}` |
| POST | `/api/cm/slo/register` | `{parameter:["<slo-id>"]}` | `{data:"ok"}` |
| POST | `/api/cm/slo/delete` | `{parameter:["<slo-id>"]}` | `{data:"ok"}` |
| POST | `/api/cm/slo/find-measurement` | `{resourceType:"<...>"}` | 사용 가능한 SLI 메트릭 |

→ [`recipes/slo.md`](./recipes/slo.md)

### 알람 정책 — 공통 정책 (Common Policy)
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/alarm/policys` | `{pageNumber, gridFilters, sortFieldSets, pagePerSize, arguments, tagFilters:null}` | `{data:{content:[{id, name, domain, tagKey:"alarmPolicy", default, ...}]}}` |
| POST | `/api/alarm/policys/add/validate/name/duplicate` | `{name, domain}` | 이름 중복 검증 |
| POST | `/api/alarm/policys/add` | `{name, description, enable, copyId:"<source-id>", tagValue, authorityInfos:[{roleId, permission:15}], domain}` | `{data:true}` (id 안 반환 — list 로 조회 필요) |
| POST | `/api/alarm/policys/delete` | `{ids:["<id>"]}` | `{data:{deletedCount, notDeletedCount, notDeletedList}}` |
| POST | `/api/alarm/policys/options` | `{}` | dropdown options |
| POST | `/api/alarm/policy/definitions` | `{policyId}` | 정책 내 정의 목록 |
| POST | `/api/alarm/policy/definitions/add` | `{...}` | 정책에 정의 추가 |
| POST | `/api/alarm/policy/definitions/delete` | `{...}` | 정책 내 정의 삭제 |

### 알람 정책 — 개별 알람 정의 (Individual Definition)
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/alarm/alarm-definitions` | `{pageNumber, gridFilters, sortFieldSets, pagePerSize, tagFilters}` | `{data:{content:[{id, name, type:"Individual", resourceId, conditions, ...}]}}` |
| POST | `/api/alarm/alarm-definitions/count` | `{}` | 개수 |
| POST | `/api/alarm/alarm-definition` | **풀 스키마**: top-level `{targetConfIds, name, description, enabled, resourceType, alarmMessageTemplate, alarmTimeout, timeoutSeverity, measurementDefinitionId, measurementType:"METRIC", measurementAlias, activeAlarmPolicy:"LAST_ONE", maxAlarmsPerMin, conditions:[...], alarmNotifications:[], triggerActions:[]}` + 각 condition `{type:"THRESHOLD", alarmSeverity, measurementDefinitionId, measurementType:"METRIC", operator, numericThreshold, conditionText, units, dampeningType:"NONE", byAi:false}` | `{data:<count>}` |
| POST | `/api/alarm/alarm-definition/detail` | `{parameter:"<id>"}` | full detail |
| POST | `/api/alarm/alarm-definition/delete` | `{parameter:["<id>"]}` | `{data:true}` |
| POST | `/api/alarm/alarm-definition/update` | (TBD body) | 정의 수정 |

> ⚠️ **NPE 함정**: 위 풀 스키마에서 `measurementType`, `measurementAlias`, `activeAlarmPolicy`, condition 의 `measurementType`, `conditionText`, `units` 중 하나라도 누락하면 detail 호출에서 NPE 발생 (UI drawer 안 열림). 메트릭 prefix (`<resourceType>_<...>`) 가 알람의 `resourceType` 과 일치 필수.

### 메트릭 카탈로그 (알람 정의 추가 시 필수)
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/measurement/definitions/resource-type` | `{parameter:{resourceType:"<type>"}}` | type-filtered 메트릭 list (스키마 풍부, `id`/`alias`/`units`/`measurementType` 등) |
| POST | `/api/measurement/definitions/category/` | `{parameter:"<resourceType>"}` | 동일 결과 (다른 키 이름) |
| POST | `/api/alarm/options/measurementDefinition` | `{}` | 전체 1404 메트릭 (필터 무시 — 클라이언트 측 필터링용) |

응답 핵심 필드 (`/api/measurement/definitions/resource-type` 기준):
- `id` ← `measurementDefinitionId` 로 사용
- `alias` ← `measurementAlias` 로 사용
- `units` ← condition 의 `units` 로 사용
- `measurementType` ← top-level + condition 양쪽에 사용
- `description` ← 사용자 prompt 용 한글 설명

→ [`recipes/add-alert-policy.md`](./recipes/add-alert-policy.md) 의 "메트릭 카탈로그 조회" 섹션 참조.

→ [`recipes/add-alert-policy.md`](./recipes/add-alert-policy.md)

### 이상감지 정책 (Anomaly Policy)
| Method | URL | body 형태 | 결과 |
|---|---|---|---|
| POST | `/api/aiops/v1/anomaly-policies/names` | `{}` | `["성능 이상감지 기본 정책", ...]` |
| POST | `/api/aiops/v1/anomaly-policies/list-filter` | `{pageNumber, gridFilters, sortFieldSets, pagePerSize, arguments, tagFilters}` | `{data:{content:[{id, name, systemCount, metricCount, isAuto, isDefault, ...}]}}` |
| POST | `/api/aiops/v1/anomaly-policies/<id>` | (빈 body) | 정책 상세 |
| POST | `/api/aiops/v1/anomaly-policies/<id>/authority` | (빈 body) | 권한 정보 |
| POST | `/api/aiops/v1/anomaly-metric-models/list-filter` | `{...}` | 메트릭 모델 목록 |

CRUD (생성/수정/삭제) 는 본 캡처에서 미확인. 시스템 default 만으로 테스트베드 운영 가능 → 후순위.

→ [`recipes/anomaly-policy.md`](./recipes/anomaly-policy.md)

### 부가 메타 / 메트릭 (참고용)
| Method | URL | 용도 |
|---|---|---|
| POST | `/api/account/menu/user-menus` | 사용자별 메뉴 트리 |
| POST | `/api/account/function/user-functionIds` | 기능 권한 ID 목록 |
| POST | `/api/account/user/self/detail` | 로그인 사용자 상세 |
| POST | `/api/alarm/severity/list` | 알람 severity 메타 |
| POST | `/api/alarm/options/measurementDefinition` | 메트릭 dropdown (정의 추가 시) |
| POST | `/api/alarm/resource/domain/options` | 도메인 dropdown |
| POST | `/api/alarm/resource/type/options` | resourceType dropdown |
| POST | `/api/alarm/resource/alarm-policy-summary` | 리소스별 알람 정책 요약 |
| POST | `/api/alarm/policy/authority` | 정책 권한 |
| POST | `/api/alarm/message-template-preview` | 알람 메시지 템플릿 프리뷰 |
| POST | `/api/measurement/availability/resource/latest` | 가용성 최신값 |
| POST | `/api/measurement/metric/aggregation/latest` | 메트릭 집계 최신값 |
| POST | `/api/measurement/metric/raw/single/time-period` | 단일 메트릭 시계열 |
| POST | `/api/measurement/definitions` | 메트릭 정의 |
| POST | `/api/measurement/policies/simple-list` | 측정 정책 목록 |

---

## TBD — 후속 캡처 필요

### Agent-based 다른 타입 (Issue 4 진행 후)

```
POST /api/dpm/preregister/list                ← HAR 에 관찰됨 (GET? POST?)
POST /api/dpm/preregister/dbtypes             ← 관찰됨
POST /api/dpm/preregister/error-count         ← 관찰됨
POST /api/dpm/<???>/register                  ← TBD

POST /api/apm/standby-agent/count             ← 관찰됨
POST /api/apm/standby-agent/new/count         ← 관찰됨
POST /api/apm/<???>/register                  ← TBD

POST /api/kcm/standby-clusters-filter-step1   ← 관찰됨
POST /api/kcm/<???>/register                  ← TBD

POST /api/nms/v1/pre/list                     ← 관찰됨
POST /api/nms/v1/<???>                        ← TBD register
POST /api/nms/trap/v1/pre/list                ← 관찰됨
POST /api/nms/v1/custom/snmpoid/pre/list      ← 관찰됨
POST /api/nms/v1/custom/script/pre/list       ← 관찰됨
```

### Config-only 다른 타입

```
POST /api/syslog/v1/pre/list                  ← 관찰됨
POST /api/sms/custom-script/pre-list-filter   ← 관찰됨
POST /api/dpm/custom/sql/prelist              ← 관찰됨
POST /api/cm/slo/list-filter                  ← 관찰됨
POST /api/rulechain/integration-systems/count ← 관찰됨
```

### 그 외

- 알람 정책 등록 (개별 정책 + 정책 그룹)
- 담당자 권한 부여 (`/api/account/*` 영역)
- 사용자 정의 항목 (Trap/Syslog/SQL/SNMP OID/Script/SLO) save+register

---

## 주요 발견 / 함정 정리

1. **`/api/cm/configuration/list` 는 catch-all 스텁** — 사용 금지. 진짜 list 는 `<type>-filter` / `<type>/list-filter`.
2. **페이징 스펙이 두 종류**:
   - 신규 endpoint: `pageNumber` (1-based) + `pagePerSize`
   - 일부 구식: `page` (0-based) + `size`
3. **Identifier 형식 type 별로 다름**: WebURL `weburl_<id>`, 서버 `MA_<...>` (그대로). 일반 prefix rule 없음.
4. **register body 가 array**: 일괄 등록 가능, 단일도 array 로 wrapping 필요.
5. **register 필드 이름 type 별 차이**: WebURL `dataPolicy`/`tag` ↔ 서버 `collectorPolicyTagValue`/`serviceGroupTagValue` (값은 같은 의미).
6. **시스템 그룹 vs 서비스 그룹은 별개 entity**: `groupId` (정수) vs `serviceGroupTagValue` (문자열 tag).
7. **Agent-based 삭제는 영구적이지 않음**: 에이전트 살아있으면 다음 heartbeat 에 standby 재진입.

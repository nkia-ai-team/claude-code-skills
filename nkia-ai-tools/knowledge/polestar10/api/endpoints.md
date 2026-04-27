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

polestar10 의 모든 관리대상 등록은 **staging → register** 2-step. staging 진입 방식이 두 가지:

| 모델 | 적용 type | staging 진입 | register 호출 시 식별자 필드 |
|---|---|---|---|
| **Config-only** | Web URL, SLO, Syslog, SQL, SNMP OID, 연계 시스템 등 | `POST /api/<type>/save` (사용자가 UI 로 +) | `id` (save 응답의 mongo id) |
| **Agent-based** | 서버, DB, APM, KCM, NMS | 에이전트 heartbeat 자동 | `agentId` (에이전트 자체 ID) |

**delete 도 식별자 형식이 type 별로 다름**:
- Web URL: `weburl_<bare-mongo-id>`
- 서버: `MA_<hostname>_<timestamp>` (그대로, prefix 없음)

→ "<type>_<id>" 패턴으로 일반화 시도했으나 실제로는 **type 별 약속이 다름**. recipe 별 확인 필요.

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

### 부가 메타 / 메트릭 (참고용)
| Method | URL | 용도 |
|---|---|---|
| POST | `/api/account/menu/user-menus` | 사용자별 메뉴 트리 |
| POST | `/api/account/function/user-functionIds` | 기능 권한 ID 목록 |
| POST | `/api/account/user/self/detail` | 로그인 사용자 상세 |
| POST | `/api/aiops/v1/anomaly-policies/names` | 이상감지 정책 이름 목록 (register 다이얼로그용) |
| POST | `/api/alarm/severity/find-all` | 알람 severity 메타 |
| POST | `/api/alarm/resource/alarm-policy-summary` | 리소스별 알람 정책 요약 |
| POST | `/api/measurement/availability/resource/latest` | 가용성 최신값 |
| POST | `/api/measurement/metric/aggregation/latest` | 메트릭 집계 최신값 |
| POST | `/api/measurement/metric/raw/single/time-period` | 단일 메트릭 시계열 |
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

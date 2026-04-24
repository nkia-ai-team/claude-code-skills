# polestar10 엔드포인트 스펙

Playwright HAR 녹화 + 인증 세션 프로브 + 크롬 DevTools 캡처로 확인한 polestar10 내부 API 명세.

- **Base URL**: `https://192.168.230.104/` (self-signed 인증서 — curl `-k`)
- **인증**: 쿠키 기반 세션 (`accessToken` / `refreshToken` JWT). **CSRF 헤더 없음**
- **Content-Type**: write/read 모두 `application/json`
- **응답 포맷**: `{success: boolean, data: <payload>, errorCode: string|null, errorMsgArgs, errorData}`

실제 실행 가능한 bash + curl 레시피는 [`recipes/`](./recipes/) 아래.

---

## 공통 — 세션 / 인증

| 항목 | 값 |
|---|---|
| 로그인 단계 | 3-step challenge-response |
| 세션 쿠키 | `accessToken` (HttpOnly, SameSite=None, Secure), `refreshToken` |
| CSRF | 없음 |
| MFA | 사용자별 설정. 비활성 시 3-step 진행, 활성 시 TOTP 경로 필요 |
| 비밀번호 해싱 | `sha512(plaintext).hex` (소문자 hex, 128자) |
| challengeResponse | `sha512(sha512(plaintext).hex + challenge).hex` |
| 세션 만료 | accessToken 1h, refreshToken ~24h (JWT exp) |

→ [`recipes/login.md`](./recipes/login.md)

---

## 관리대상 등록 — 범용 2-step 패턴

polestar10 의 **모든 리소스 타입** 은 "staging 추가 → 그룹·정책 바인딩" 2단계로 관리대상 승격:

```
Step 1: POST /api/<type>/save        → staging 리스트에 항목 생성, id 반환
Step 2: POST /api/<type>/register    → body 는 array. id + groupId + policy 바인딩 후 관리대상 승격
```

UI 매핑:
- Step 1 = "관리대상 추가" 다이얼로그의 **+ 버튼 → 저장**
- Step 2 = 다이얼로그 하단 **관리대상 등록** 버튼 → 그룹·정책 선택 → 저장

### agent 기반 vs config 기반 차이

| 모델 | 리소스 타입 | Step 1 방식 |
|---|---|---|
| **agent-heartbeat** | 서버, DB, APM, KCM, NMS | 타겟에 에이전트 설치 → heartbeat → polestar10 이 standby 자동 추가 (`save` 없이 자동 생성) |
| **config-only** | Web URL, 연계 시스템, 사용자정의 항목 | UI `+` 버튼으로 사용자 직접 `save` 호출 |

→ Step 2 (`register`) 는 두 모델 모두 동일한 흐름.
→ 본 스펙은 Web URL (config-only) 까지 확정. agent 기반 타입은 Issue 4 Ansible 플레이북으로 실제 에이전트 설치 후 DevTools 캡처로 확정 예정 (TBD).

---

## 확정된 엔드포인트

### 1. 로그인 (3-step)

| # | Method | URL | 입출력 요약 |
|---|---|---|---|
| 1-1 | POST | `/api/account/pre-login` | in: `{loginId, password=sha512(pwd)}` out: `{challenge, organizations[]}` |
| 1-2 | POST | `/api/cm/two-factor-authentication/enable` | in: `{parameter:"SECONDARY_CERTIFICATION"}` out: `{enable, email, sms, otp}` |
| 1-3 | POST | `/api/account/login` | in: `{loginId, challenge, challengeResponse, organizationId}` out: `{userId, ...}`, Set-Cookie accessToken/refreshToken |

→ [`recipes/login.md`](./recipes/login.md)

### 2. 리소스 그룹 조회

| Method | URL | 입출력 |
|---|---|---|
| POST | `/api/cm/groups/list` | in: `{}` out: `[{id, name, description, groupType, ...}]` — 기본 Default(id=1), Root(id=0) 포함 |

→ [`recipes/list-groups.md`](./recipes/list-groups.md)

### 3. 관리대상 개수 조회

| Method | URL | 입출력 | 비고 |
|---|---|---|---|
| POST | `/api/cm/portal/configuration/count` | in: `{}` out: `{data: <total int>}` | 전 타입 합산 |
| POST | `/api/weburl/count` | in: `{}` out: `{data: <int>}` | WebURL 만 |
| POST | `/api/<type>/count` | — | 타입별. 패턴 확인됨. server/DB/APM 은 TBD |

→ [`recipes/list-targets.md`](./recipes/list-targets.md)

> ⚠️ `POST /api/cm/configuration/list` 는 **사용 금지**. catch-all 스텁으로 항상 빈 `configItems:[]` 반환 (초기 오판 후 검증으로 확인).

### 4. Web URL 등록 (save + register)

| # | Method | URL | 입출력 요약 |
|---|---|---|---|
| 4-1 | POST | `/api/weburl/save` | in: `{name, url, method, connectTimeout, socketTimeout, useProxy, useSni, sslVerify, successCode, requestBodyType, description}` out: `{id, ..., registered:false}` |
| 4-2 | POST | `/api/weburl/register` | in: `[{id, dataPolicy, tag, anomalyPolicyTagValue, groupId}]` (**array!**) out: `{data:null}` |

→ [`recipes/add-target.md`](./recipes/add-target.md) — Web URL 섹션

### 5. Web URL 삭제

| Method | URL | 입출력 |
|---|---|---|
| POST | `/api/weburl/delete` | in: `{parameter:["weburl_<id>", ...]}` out: `{data:"ok"}` |

**중요**: `parameter` 배열의 각 값은 `<type>_<id>` 접두사 형식. WebURL 은 `weburl_<id>`. 다른 타입도 동일 패턴(예: `server_<id>`) 로 추정.

→ [`recipes/delete-target.md`](./recipes/delete-target.md)

---

## TBD 엔드포인트

### 서버/DB/APM/K8s/NMS — Agent-heartbeat 기반

| 조작 | 가설 경로 prefix | 확정 대기 사유 |
|---|---|---|
| 서버 save/register | `/api/sms/hosts/*` (referer 에서 추론) | WPM agent heartbeat 필요 → Issue 4 선행 |
| DB save/register | `/api/dpm/*` | DPM agent + DB 접속 정보 필요 |
| APM save/register | `/api/apm/*` | APM agent 필요 |
| K8s save/register | `/api/kcm/*` | KCM agent 필요 |
| NMS 네트워크 register | `/api/nms/*` | SNMP 타겟 또는 NMS agent 필요 |

### 기타

| 조작 | 가설 | 사유 |
|---|---|---|
| 담당자 권한 부여 | `/api/account/*` | 관리자 roles 구조 탐색 필요 |
| 개별 알람 정책 등록 | `/api/alarm/*` | severity 메타 선행 조회 필요 |
| 세부 list (항목 상세) | `/api/<type>/list` (WebURL 은 404, 다른 이름) | 각 타입의 목록 페이지 HAR 캡처 필요 |

각 TBD 의 확정 절차는 [README.md](./README.md#tbd-엔드포인트-확정-절차) 참조.

---

## 부가 엔드포인트 (로그인 HAR 에서 관찰됨, 참고용)

```
POST /api/account/menu/user-menus              # 사용자별 메뉴 트리
POST /api/account/function/user-functionIds    # 기능 권한 ID 목록
POST /api/account/user/self/detail             # 로그인 사용자 상세
POST /api/account/user/profile                 # 프로필
POST /api/account/user/personalization         # UI 개인화
POST /api/account/token/valid                  # 토큰 유효성 체크
POST /api/account/logout                       # 로그아웃
POST /api/account/license/enable-by-product    # 라이선스 상태
POST /api/account/license/count
POST /api/cm/groups/tree                       # 그룹 트리 (flat 이 아닌 계층)
POST /api/cm/portal/configuration/count
POST /api/cm/portal/maintenance/count
POST /api/cm/portal/measurement-availability
POST /api/alarm/severity/find-all              # 알람 severity 메타
POST /api/alarm/view/portal/count-by-severity
POST /api/event/view/severity/list
POST /api/event/view/portal/count
POST /api/aiops/v1/resources/anomaly-status-latest
POST /api/aiops/v1/anomaly-policies/names      # 이상감지 정책 목록 (register 다이얼로그용)
POST /api/meta/portal/search-text/recommend-search-text
POST /api/sms/custom-monitor/count
POST /api/nms/trap/v1/custom-monitor/count
POST /api/nms/v1/custom/snmpoid/count
POST /api/nms/v1/custom/script/count
POST /api/dpm/custom/sql/count
POST /api/syslog/v1/custom-monitor/count
POST /api/weburl/count                         # 위 확정 섹션 참조
POST /api/rulechain/integration-systems/count
POST /api/message/last-update-time
POST /api/message/noauth/default/all           # 공지
POST /api/account/noauth/login-view
POST /api/account/noauth/locale
```

# polestar10 엔드포인트 스펙

Playwright HAR 녹화 + 인증 세션 프로브로 확인한 polestar10 내부 API 명세.

- **Base URL**: `https://192.168.230.104/` (self-signed 인증서 — curl `-k`)
- **인증**: 쿠키 기반 세션 (`accessToken` / `refreshToken` JWT). **CSRF 헤더 없음**
- **Content-Type**: write/read 모두 `application/json`
- **응답 포맷**: `{success: boolean, data: <payload>, errorCode: string|null, errorMsgArgs, errorData}`

실제 실행 가능한 bash + curl 레시피는 [`recipes/`](./recipes/) 아래.

---

## 공통 — 세션 / 인증

| 항목 | 값 | 근거 |
|---|---|---|
| 로그인 단계 | 3-step challenge-response | HAR `01-login.har` |
| 세션 쿠키 | `accessToken` (HttpOnly, SameSite=None, Secure), `refreshToken` | `/api/account/login` Set-Cookie |
| CSRF | 없음 | write 요청에서 CSRF 헤더 미관찰 |
| MFA | 사용자별 설정. 비활성 시 3-step 진행, 활성 시 TOTP 경로 필요 | `/api/cm/two-factor-authentication/enable` 응답 |
| 비밀번호 해싱 | `sha512(plaintext).hex` (소문자 hex, 128자) | pre-login body 와 `sha512('<actual-pwd>')` 일치 검증 |
| challengeResponse | `sha512(sha512(plaintext).hex + challenge).hex` | login body 와 계산값 일치 검증 |
| 세션 만료 | accessToken 1h, refreshToken ~24h (JWT exp 필드) | 디코딩된 JWT payload |

---

## 1. 로그인 (3-step)

### 1-1. `POST /api/account/pre-login`
| 항목 | 값 |
|---|---|
| Required body | `{"loginId": "...", "password": "<sha512hex(plaintext)>"}` |
| Success response | `{"success": true, "data": {"challenge": "<64-hex>", "organizations": [{"organizationId": "...", "name": "..."}]}, "errorCode": null}` |
| Failure | `errorCode` 에 사유. `data` 가 `null` 이거나 organizations 가 빈 배열이면 로그인 불가 |

### 1-2. `POST /api/cm/two-factor-authentication/enable`
| 항목 | 값 |
|---|---|
| Required body | `{"parameter": "SECONDARY_CERTIFICATION"}` |
| Success response | `{"success": true, "data": {"enable": false, "email": false, "sms": false, "otp": false}}` — 모두 false 면 1-3 즉시 진행 가능 |
| 비고 | MFA 설정 유무를 조회. sjbang 테스트 계정 기준으로 전 항목 false (MFA 비활성) |

### 1-3. `POST /api/account/login`
| 항목 | 값 |
|---|---|
| Required body | `{"loginId": "...", "challenge": "<from pre-login>", "challengeResponse": "<sha512(hash+challenge)>", "organizationId": "<from pre-login>"}` |
| Success response | `{"success": true, "data": {"userId": "...", "loginId": "...", "organizationId": "...", "organizationName": "...", "roleIds": [...]}}`, Set-Cookie `accessToken` + `refreshToken` |
| Failure | `errorCode` 에 사유 |

→ [`recipes/login.md`](./recipes/login.md) 참조.

---

## 2. 관리대상 목록 조회

### `POST /api/cm/configuration/list`
| 항목 | 값 |
|---|---|
| Required body | `{"page": <int>, "size": <int>}` — 기본 `{"page": 0, "size": 50}` |
| Optional body | `"resourceType": "<TYPE>"` — 필터 (예: `"SERVER"`, `"NMS"`, `"APM"`, `"KCM"`, `"WEBURL"`, `"ORACLE"`, `"CUBRID"`, `"POSTGRESQL"`, `"TIBERO"`, `"SQLSERVER"`, `"MYSQL"`, `"MARIADB"`, `"LINKAGE_SYSTEM"`) |
| Success response | `{"success": true, "data": {"configItems": [<target>...], "latestTimestamp": <epoch_ms>}}` |
| Alias (동작 동일) | `/list`, `/search`, `/find-all`, `/paging`, `/list-paging`, `/page`, `/find` 모두 같은 핸들러에 매핑. `list` 가 canonical |

**중요**: `/api/cm/configuration/<anything>` POST 는 대부분 200 + 빈 기본 응답을 반환하는 **catch-all 핸들러** 가 걸려있음. 이 때문에 write endpoint 를 guessing 으로 찾는 것은 불가능 — 실제 UI 제출 시 DevTools 로 URL 을 직접 확보해야 함.

→ [`recipes/list-targets.md`](./recipes/list-targets.md) 참조.

---

## 3. 리소스 그룹 조회

### `POST /api/cm/groups/list`
| 항목 | 값 |
|---|---|
| Required body | `{}` (빈 객체) |
| Success response | `{"success": true, "data": [{"id": <int>, "name": "<string>", "description": "<string>", "groupType": "<string>", ...}]}` |
| 비고 | 기본적으로 `Default`, `Root` 그룹이 포함 |

→ [`recipes/list-groups.md`](./recipes/list-groups.md) 참조.

---

## 4~9. Write 엔드포인트 — TBD

다음 조작들은 **엔드포인트 미확정** 상태. 각 recipe 파일의 TBD 섹션 + [README.md 의 확정 절차](./README.md#tbd-엔드포인트-확정-절차) 참조:

| 조작 | Recipe | 추정 경로 prefix | 상태 |
|---|---|---|---|
| 관리대상 추가 | [`recipes/add-target.md`](./recipes/add-target.md) | `/api/cm/configuration/*` | TBD |
| 관리대상 삭제 | [`recipes/delete-target.md`](./recipes/delete-target.md) | `/api/cm/configuration/*` | TBD |
| 담당자 권한 부여 | [`recipes/assign-owner.md`](./recipes/assign-owner.md) | `/api/account/*` | TBD |
| NMS 네트워크 등록 | [`recipes/register-nms.md`](./recipes/register-nms.md) | `/api/nms/*` | TBD |
| DPM 등록 | [`recipes/register-dpm.md`](./recipes/register-dpm.md) | `/api/dpm/*` | TBD |
| 개별 알람 정책 등록 | [`recipes/add-alert-policy.md`](./recipes/add-alert-policy.md) | `/api/alarm/*` | TBD |

---

## 로그인 HAR 에서 발견된 부가 엔드포인트 (참고용)

다음은 로그인 + 대시보드 초기 로드 시 관찰된 엔드포인트 목록. 향후 스킬 기능 확장 시 출발점:

```
POST /api/account/menu/user-menus              # 사용자별 접근 가능 메뉴 트리
POST /api/account/function/user-functionIds    # 사용자 기능 권한 ID 목록
POST /api/account/user/self/detail             # 로그인 사용자 상세
POST /api/account/user/profile                 # 프로필
POST /api/account/user/personalization         # UI 개인화 설정
POST /api/account/token/valid                  # 토큰 유효성 체크
POST /api/account/license/enable-by-product    # 라이선스 활성화 상태
POST /api/account/license/count
POST /api/cm/groups/tree                       # 리소스 그룹 트리
POST /api/cm/portal/configuration/count
POST /api/cm/portal/maintenance/count
POST /api/cm/portal/measurement-availability
POST /api/alarm/severity/find-all              # 알람 severity 메타
POST /api/alarm/view/portal/count-by-severity
POST /api/event/view/severity/list
POST /api/event/view/portal/count
POST /api/aiops/v1/resources/anomaly-status-latest
POST /api/meta/portal/search-text/recommend-search-text
POST /api/sms/custom-monitor/count
POST /api/nms/trap/v1/custom-monitor/count
POST /api/nms/v1/custom/snmpoid/count
POST /api/nms/v1/custom/script/count
POST /api/dpm/custom/sql/count
POST /api/syslog/v1/custom-monitor/count
POST /api/weburl/count
POST /api/rulechain/integration-systems/count
POST /api/message/last-update-time
POST /api/message/noauth/default/all           # 공지 메시지
POST /api/account/noauth/login-view            # 로그인 화면 설정
POST /api/account/noauth/locale                # 로케일
POST /api/account/logout                       # 로그아웃
```

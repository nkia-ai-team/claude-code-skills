# polestar10 엔드포인트 스펙 (NKIAAI-539 AC2)

Playwright HAR 녹화(`har-captures/`) 및 인증 세션 프로브로 확인한 엔드포인트.

**Target base URL**: `https://192.168.230.104/`
**인증 방식**: 쿠키 기반 세션 (`accessToken`, `refreshToken` JWT). **CSRF 토큰 없음** — 헤더에 별도 토큰 주입 불필요.

---

## 공통 — 인증 / 세션

| 항목 | 값 | 근거 |
|---|---|---|
| 로그인 단계 | 3-step challenge-response | `01-login.har` entries 8~10 |
| 세션 쿠키 | `accessToken` (HttpOnly, SameSite=None, Secure), `refreshToken` | `/api/account/login` Set-Cookie |
| CSRF | 없음 | 모든 write 요청에서 CSRF 헤더 미사용 |
| MFA | 사용자별 설정. sjbang: 비활성 (`enable:false, email:false, sms:false, otp:false`) | `/api/cm/two-factor-authentication/enable` 응답 |
| 비밀번호 해싱 | `sha512(pwd).hexdigest()` (소문자 hex, 128자) | 관찰된 pre-login body 와 `sha512('qkd016610!')` 일치 |
| challengeResponse | `sha512(sha512(pwd).hex + challenge).hex` | 관찰된 challengeResponse 와 일치 |

**클라이언트가 `FallThroughRequired` 를 raise 하는 조건**
1. MFA 활성 계정 (현 구현은 TOTP 미지원)
2. `pre-login` 이 `organizations` 를 비어서 반환
3. 본 문서에 `TBD` 로 표기된 엔드포인트를 호출
4. 응답 body 가 `{success:false}` 또는 HTML(세션 만료로 redirect)

---

## 1. 로그인 (3-step)

### 1-1. `POST /api/account/pre-login`
| 항목 | 값 |
|---|---|
| Content-Type | `application/json` |
| Required body | `{loginId, password: sha512Hex(plaintext)}` |
| Success response | `{success:true, data:{challenge, organizations:[{organizationId, name}]}, errorCode:null}` |

### 1-2. `POST /api/cm/two-factor-authentication/enable`
| 항목 | 값 |
|---|---|
| Required body | `{parameter: "SECONDARY_CERTIFICATION"}` |
| Success response | `{success:true, data:{enable, email, sms, otp}}` — 모두 false 면 1-3 즉시 진행 |

### 1-3. `POST /api/account/login`
| 항목 | 값 |
|---|---|
| Required body | `{loginId, challenge, challengeResponse, organizationId}` |
| Success response | `{success:true, data:{userId, loginId, organizationId, organizationName, roleIds:[...]}}`, Set-Cookie `accessToken` + `refreshToken` |

---

## 2. 관리대상 목록 조회 (list_targets)

| 항목 | 값 |
|---|---|
| URL | `POST /api/cm/configuration/list` |
| Required body | `{page:int, size:int}` (기본 `{page:0, size:50}`) |
| Optional body | `resourceType:str` (예: `"SERVER"`, `"NMS"`, `"APM"`, `"KCM"`, `"WEBURL"`, `"CUBRID"`, ...) |
| Success response | `{success:true, data:{configItems:[...], latestTimestamp:<ms>}}` |
| 비고 | Spring 에 `list` / `search` / `find-all` / `paging` / `list-paging` / `page` / `find` 가 동일 핸들러 별칭으로 매핑됨. `list` 가 canonical. |

**Alias (동작 동일)**: `/list`, `/search`, `/find-all`, `/paging`, `/list-paging`, `/page`, `/find`

## 3. 리소스 그룹 조회 (list_groups)

| 항목 | 값 |
|---|---|
| URL | `POST /api/cm/groups/list` |
| Required body | `{}` |
| Success response | `{success:true, data:[{id, name, description, groupType, ...}]}` — 기본 `Default`, `Root` 그룹 포함 |

---

## 4. 관리대상 추가 (add_target) — **TBD**

현재 구현은 `FallThroughRequired` raise.

| 항목 | 값 |
|---|---|
| URL | **TBD** — SPA 가 /config/resource/all URL 을 직접 라우팅하지 않으며, 관리대상 추가 다이얼로그는 라이선스드 위젯 번들에 의존. |
| 해결 경로 | (1) 운영자 1명이 Playwright headed 모드에서 전체구성 > 관리대상 > 리소스타입 선택 > + 추가 클릭 → 폼 제출, HAR 녹화. (2) HAR 에서 POST URL/payload 추출. (3) 본 섹션 + `client.py.add_target` 업데이트. |
| Alias 추정 | `/api/cm/configuration/<type>/register`, `/api/cm/configuration/save` 중 하나. Spring catch-all 핸들러가 모든 `/api/cm/configuration/**` POST 에 대해 `{configItems:[]}` 를 반환하므로 guessing 만으로 실제 endpoint 확정 불가 (관찰 사실). |

## 5. 관리대상 삭제 (delete_target) — **TBD**

현재 구현은 `FallThroughRequired` raise. `add_target` 과 동일한 절차로 스키마 추출 필요.

## 6. 담당자 권한 부여 (assign_owner) — **TBD**

`FallThroughRequired`. `/api/account/*` 경로 탐색 필요. `roleIds` 를 업데이트하는 엔드포인트로 추정.

## 7. NMS 네트워크 등록 (register_nms) — **TBD**

`FallThroughRequired`. `/api/nms/*` 경로. `/api/nms/trap/v1/custom-monitor/count` 가 로그인 HAR 에 관찰되므로 NMS 서비스는 `/api/nms/` 또는 `/api/nms/v1/` prefix 사용.

## 8. DPM 등록 (register_dpm) — **TBD**

`FallThroughRequired`. `/api/dpm/*` 경로. `/api/dpm/custom/sql/count` 가 HAR 에 관찰됨.

## 9. 개별 알람 정책 등록 (add_alert_policy) — **TBD**

`FallThroughRequired`. `/api/alarm/*` 경로. `/api/alarm/severity/find-all` 이 HAR 에 관찰됨. Severity 메타데이터가 먼저 필요할 가능성 있음.

---

## Spring catch-all 현상

**중요 관찰**: `/api/cm/configuration/**` 하위의 많은 경로(`save`, `create`, `add`, `register`, `remove`, `delete`, `schema`, `field/all`, `server/save` 등)가 모두 200 OK + `{success:true, data:{configItems:[], latestTimestamp:null}}` 를 반환한다. 이는 cm 서비스의 `@PostMapping("/configuration/**")` 가 catch-all 로 동작하거나, 인증만 통과하면 기본 응답을 반환하는 핸들러가 걸려있음을 시사. 이 때문에 guessing 으로 write endpoint 확정 불가 — **반드시 실제 UI 제출의 HAR 이 필요.**

## TBD 해결 절차 (follow-up 이터레이션)

```bash
# 1. 운영자가 실행 — headed Chromium 으로 직접 클릭
POLESTAR10_HEADED=1 .venv/bin/playwright codegen https://192.168.230.104/login

# 2. 로그인 → 전체구성 > 관리대상 > (Server 등) > + 추가 클릭 → 폼 제출
#    codegen 창에서 생성되는 Python 코드를 scripts/02_add_target.py 에 반영

# 3. 네트워크 탭에서 POST URL + payload JSON 을 확인하여
#    client.py.add_target() 본문을 작성하고 FallThroughRequired 제거

# 4. pytest 로 login → add → list(신규 포함) → delete 라운드트립 초록 확인
```

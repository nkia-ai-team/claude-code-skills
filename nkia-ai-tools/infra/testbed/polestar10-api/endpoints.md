# polestar10 엔드포인트 스펙 (NKIAAI-539 AC2)

Playwright HAR 녹화(`har-captures/`) 에서 추출한 엔드포인트 사양.

**Target base URL**: `https://192.168.230.104/`
**인증 방식**: (HAR 분석 후 채워짐 — 쿠키 기반 세션 + CSRF 토큰 추정)

---

## 공통 — 인증 / CSRF

| 항목 | 값 | 근거 HAR |
|---|---|---|
| 세션 쿠키 이름 | TBD | `01-login.har` |
| CSRF 헤더 이름 | TBD (예: `X-XSRF-TOKEN`) | `01-login.har` |
| CSRF 전달 방식 | TBD (쿠키 → 헤더 재주입 또는 meta 태그) | `01-login.har` |
| 로그아웃 | TBD | — |

클라이언트가 `FallThroughRequired` 를 raise 하는 조건:

1. `401/403` — 세션 만료이되 재로그인 2회 실패 시
2. `4xx` with payload missing known fields — 스키마 드리프트
3. 응답 body 가 HTML (즉, 인증 redirect) 일 때 — 세션 문제

---

## 1. 로그인

| 항목 | 값 |
|---|---|
| URL | TBD (예: `POST /api/auth/login`) |
| Method | `POST` |
| Required fields | `username`, `password` |
| Optional fields | — |
| Success schema | `{ "token": "...", "user": { ... } }` (TBD) |
| Notes | 로그인 성공 시 Set-Cookie 로 세션 심는지 확인 |

## 2. 관리대상 추가 (add_target)

| 항목 | 값 |
|---|---|
| URL | TBD |
| Method | `POST` |
| Required fields | `name`, `ip` |
| Optional fields | `description`, `tags[]` |
| Success schema | `{ "id": "...", "name": "...", ... }` |

## 3. 관리대상 목록 조회 (list_targets)

| 항목 | 값 |
|---|---|
| URL | TBD |
| Method | `GET` |
| Query | `page`, `size`, `q` |
| Success schema | `{ "items": [...], "total": N }` |

## 4. 관리대상 삭제 (delete_target)

| 항목 | 값 |
|---|---|
| URL | TBD (예: `DELETE /api/targets/{id}`) |
| Method | `DELETE` |
| Success schema | 204 No Content |

## 5. 담당자 권한 부여 (assign_owner)

| 항목 | 값 |
|---|---|
| URL | TBD |
| Method | `POST` / `PUT` |
| Required fields | `targetId`, `userId`, `role` |

## 6. NMS 네트워크 등록 (register_nms)

| 항목 | 값 |
|---|---|
| URL | TBD |
| Method | `POST` |
| Required fields | `name`, `cidr`, `snmpCommunity`? |

## 7. DPM 등록 (register_dpm)

| 항목 | 값 |
|---|---|
| URL | TBD |
| Method | `POST` |
| Required fields | TBD |

## 8. 개별 알람 정책 등록 (add_alert_policy)

| 항목 | 값 |
|---|---|
| URL | TBD |
| Method | `POST` |
| Required fields | `metric`, `threshold`, `severity` |

---

## TBD 항목 채우기 절차

1. `POLESTAR10_USER` / `POLESTAR10_PASS` 설정
2. `for s in scripts/0*.py; do python "$s"; done`
3. `jq '.log.entries[] | {url: .request.url, method: .request.method, status: .response.status}' har-captures/*.har`
   로 요청 목록 확인
4. 각 섹션 TBD 값 채우기 + `src/polestar10_client/client.py` 메서드 본문에 반영

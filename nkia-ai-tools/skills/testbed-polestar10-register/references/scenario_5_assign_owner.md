# Scenario 5 — 담당자 권한 부여 (TBD fallback)

> "plopvape-db 담당자 sjbang 으로 지정해줘"
> "이 자원 권한 어드민한테 줘"

⚠️ **현재 상태: API 미확정 (TBD)** — 본 시나리오는 UI fallback 만 안내한다.

---

## Trigger 키워드

`담당자`, `권한`, `오너`, `owner`, `permission`, `RBAC`, `누가 볼`

---

## 현재 상황

- recipe `recipes/assign-owner.md` 는 TBD 상태 ([knowledge/polestar10/api/README.md](../../../knowledge/polestar10/api/README.md) 디렉터리 표 참조)
- DevTools HAR 캡처 미완 — 실제 POST URL 과 payload 확정 안 됨
- 일부 endpoint 는 알려져 있으나 (예: `/api/alarm/policy/authority`, `/api/aiops/v1/anomaly-policies/<id>/authority`) 자원 단위 owner 부여 endpoint 와는 다름

---

## Dispatch flow (현 시점)

```
1. 의도 확인
   - 자원 단위 owner    → 본 시나리오 (TBD)
   - 알람 정책 권한      → 일부 자동화 가능 (authorityInfos 필드, recipes/add-alert-policy.md 의 add 참조)
   - 이상감지 정책 권한  → /api/aiops/v1/anomaly-policies/<id>/authority (read-only — write TBD)
   - 사용자/역할 관리     → 본 스킬 범위 밖 (account 도메인)

2. 자원 단위 owner 인 경우 — UI fallback
   사용자에게 표시:

     polestar10 의 자원별 담당자 부여 API 는 아직 확정되지 않았습니다.
     UI 에서 진행해 주세요:
       전체구성 > 관리대상 > [자원타입] → 행 선택 → 우측 상단 [권한] 또는
       자원 상세 페이지 > authorityInfos 패널 → 사용자/역할 추가

   + 캡처 절차 가이드 (아래 섹션) 안내 — 사용자가 직접 갱신 가능

3. 알람 정책 권한 인 경우 — 자동화 가능
   recipes/add-alert-policy.md 의 add 호출 시 authorityInfos 필드 사용:
     {authorityInfos: [{roleId: "<24-hex>", permission: 15}]}
   permission: 15 = 모든 권한 (R/W/D/관리)
   roleId 는 사용자에게 dropdown 으로 입력받기 (현재 role list endpoint 도 TBD)
```

---

## 캡처 절차 가이드 (사용자가 직접 캡처할 때)

[knowledge/polestar10/api/README.md "TBD 엔드포인트 확정 절차"](../../../knowledge/polestar10/api/README.md) 와 동일:

```
1. 크롬에서 polestar10 로그인
2. F12 → Network 탭, "Preserve log" 체크
3. UI 에서 자원에 담당자 부여 작업 수행 (저장 클릭까지)
4. Network 패널에서 해당 POST 요청 선택
5. Headers / Payload / Response 복사 → recipes/assign-owner.md 의 TBD 섹션 교체
```

캡처 후 본 시나리오 흐름의 "UI fallback" 안내는 자동화로 승격.

---

## 부분 자동화 정리

| 권한 종류 | 현재 | 비고 |
|---|---|---|
| **자원 단위 owner** | UI fallback 만 | TBD |
| 알람 정책 권한 (`authorityInfos`) | 자동화 (add 시점) | recipes/add-alert-policy.md |
| 이상감지 정책 권한 (read) | 자동화 (조회만) | `/api/aiops/v1/anomaly-policies/<id>/authority` |
| 이상감지 정책 권한 (write) | UI fallback 만 | TBD |
| 사용자/역할 CRUD | 본 스킬 범위 밖 | account 도메인 별도 sub-skill |

---

## 사용자에게 보여줄 메시지 템플릿

```
ℹ️ 자원 단위 담당자 부여는 polestar10 web API 가 아직 확정되지 않아
   UI 에서 직접 진행해 주세요.

   경로: 전체구성 > 관리대상 > <자원타입> → <자원 행 선택>
        → 우측 [권한] 패널 → [추가] → 사용자/역할 선택 → 저장

   ▸ 이 작업 후 endpoint 캡처가 가능하면 recipes/assign-owner.md 의 TBD 섹션을 갱신해 주세요.
     다음 호출부터 자동화됩니다 (캡처 절차는 위 "캡처 절차 가이드" 섹션 참조).
```

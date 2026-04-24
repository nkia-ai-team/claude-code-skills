# Recipe: 관리대상 삭제 (TBD)

polestar10 에서 관리대상 제거.

- **엔드포인트**: **TBD**
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: polestar10 전역 상태 변경 (레코드 제거)

## ⚠️ 현재 상태: 미확정

사유는 `recipes/add-target.md` 와 동일 (Spring catch-all, SPA 라우팅).

## 확정 절차

`recipes/add-target.md` Step 4 의 roundtrip 테스트 중 **삭제** 요청을 함께 캡처:

1. `add-target` 으로 방금 만든 테스트 관리대상을 **행 우클릭 > 삭제** 또는 체크박스 선택 후 삭제 버튼
2. 확인 다이얼로그에서 **삭제** 확정
3. DevTools Network 에서 발생한 요청 — `DELETE /...` 또는 `POST /.../delete` 혹은 `POST /.../remove` 중 성공 응답을 반환하는 요청 식별
4. URL + payload (ID 배열인지 단일 ID 인지) 확인

## 레시피 (확정 후 작성)

```bash
# TODO: DevTools 캡처 후 아래 블록 작성
#
# TARGET_ID="<id-from-list-targets>"
#
# curl $POLESTAR10_CURL_OPTS -X POST \
#   --cookie "$POLESTAR10_COOKIE_JAR" \
#   -H 'Content-Type: application/json' \
#   -d "$(jq -cn --arg id "$TARGET_ID" '{ids:[$id]}')" \
#   "$POLESTAR10_BASE_URL/api/cm/configuration/<TBD>"
```

## UI Fallback

> **전체구성 > 관리대상** 목록에서 해당 행 체크 → 상단 **삭제** 버튼 → 확인.

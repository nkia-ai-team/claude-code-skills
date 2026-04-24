# Recipe: 개별 알람 정책 등록 (TBD)

특정 관리대상 또는 메트릭에 대한 알람 정책을 신규 등록.

- **엔드포인트**: **TBD** (추정 prefix: `/api/alarm/*`)
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: 알람 발송 규칙 추가 (잘못된 설정 시 노이즈 대량 발생 가능)

## ⚠️ 현재 상태: 미확정

## 힌트 — 로그인 HAR 에서 관찰된 관련 엔드포인트

```
POST /api/alarm/severity/find-all               # severity 메타 조회
POST /api/alarm/view/portal/count-by-severity
POST /api/event/view/severity/list
```

→ 알람 서비스는 `/api/alarm/` prefix. 정책 등록 전 severity 메타 먼저 조회해야 할 가능성.

## 확정 절차

1. **알람 > 정책 관리** 메뉴 진입
2. **+ 개별 정책 등록** 버튼
3. 필드 입력:
   - 대상 (리소스 선택)
   - 메트릭 (예: CPU 사용률, 메모리 사용률)
   - 임계값 (Warning/Critical)
   - Severity
   - 수신자 / 채널
4. **저장** → DevTools Network 에서 POST 요청 식별

## 레시피 (확정 후 작성)

```bash
# 1) (선행) 사용 가능한 severity 코드 조회
# curl $POLESTAR10_CURL_OPTS -X POST \
#   --cookie "$POLESTAR10_COOKIE_JAR" \
#   -H 'Content-Type: application/json' \
#   -d '{}' \
#   "$POLESTAR10_BASE_URL/api/alarm/severity/find-all"
#
# 2) 정책 생성 — TODO: DevTools 캡처 후 작성
```

## UI Fallback

> **알람 > 정책 관리 > 개별 정책** 에서 수동 등록. NKIAAI-542 오케스트레이터는 SRE 추천 임계값을 제시하고 사용자가 UI 에서 입력하는 하이브리드 경로 제공 예정.

# Recipe: 관리대상 추가 (TBD)

관리대상(서버/DB/APM/NMS 등)을 polestar10 에 신규 등록.

- **엔드포인트**: **TBD**
- **인증 필요**: `recipes/login.md` 먼저 실행
- **부작용**: polestar10 전역 상태 변경 (신규 레코드 생성)

## ⚠️ 현재 상태: 미확정

이 조작의 POST URL + payload 스키마는 **아직 확정되지 않음**.

사유:
- Spring `cm` 서비스가 `/api/cm/configuration/**` 하위에 catch-all 핸들러 걸어둠 → 경로 guessing 시 대부분 200 + 빈 응답 반환
- React SPA 가 `/config/resource/all` 같은 URL 을 직접 라우팅하지 않아 Playwright 자동 녹화로 추가 다이얼로그 진입 불가
- 관리대상 등록 다이얼로그는 리소스타입 선택 → 동적 폼 렌더링이라 스키마가 resourceType 별로 다를 가능성 높음

## 확정 절차

**담당자가 크롬 DevTools 로 직접 녹화해야 함.**

### Step 1: DevTools 세션 시작

1. 크롬 탭에서 `https://192.168.230.104/login` 접속 (self-signed 경고 무시)
2. `F12` → **Network** 탭 선택
3. 톱니바퀴 설정에서:
   - ☑ Preserve log
   - ☑ Disable cache
4. 정상 로그인 (sjbang 등)

### Step 2: 대상 조작 수행

1. 좌측 사이드바: **전체구성 > 관리대상 > (SERVER 등 리소스타입)** 클릭
2. 우측 상단 **+ 추가** 버튼
3. 폼 채우기:
   - 이름: `nkiaai539-probe-<random>`
   - IP: `10.250.250.250` (또는 실제 테스트용 IP)
   - 그룹: `Default`
   - 기타 필드 기본값
4. **저장** 버튼 클릭

### Step 3: 네트워크 요청 캡처

1. Network 패널에서 **Filter: Fetch/XHR** 로 좁히기
2. 저장 직후 발생한 `POST` 요청 중 응답이 `{success:true}` + `data.id` 를 반환하는 엔드포인트 식별
3. 해당 요청 **우클릭 > Copy > Copy as cURL (bash)** 로 복사
4. Request Payload JSON 구조 확인 (특히 resourceType 별 required fields)

### Step 4: 정리

1. 방금 만든 테스트 관리대상 **삭제** (roundtrip 이므로 delete 요청도 같이 캡처 → `recipes/delete-target.md` 업데이트)
2. 캡처한 URL + payload 를 이 파일의 **레시피** 섹션으로 옮기고 TBD 마커 제거
3. PR 로 반영

## 레시피 (확정 후 작성)

```bash
# TODO: DevTools 캡처 후 아래 블록 작성
#
# : "${POLESTAR10_BASE_URL:=https://192.168.230.104}"
# : "${POLESTAR10_COOKIE_JAR:=/tmp/polestar10.cookies}"
# : "${POLESTAR10_CURL_OPTS:=-sk}"
#
# curl $POLESTAR10_CURL_OPTS -X POST \
#   --cookie "$POLESTAR10_COOKIE_JAR" \
#   -H 'Content-Type: application/json' \
#   -d '{"...": "..."}' \
#   "$POLESTAR10_BASE_URL/api/cm/configuration/<TBD>"
```

## 예상 응답 스키마 (확정 후 검증)

```json
{
  "success": true,
  "data": {
    "id": "<string>",
    "name": "<string>",
    "resourceType": "<string>",
    "...": "..."
  },
  "errorCode": null
}
```

## UI Fallback (API 확정 전 유일한 경로)

> **전체구성 > 관리대상 > [리소스타입] > + 추가** 로 UI 에서 수동 등록. 필수 필드:
> - 이름 (중복 불가)
> - IP (리소스타입에 따라 포트도 필요)
> - 그룹 (기본 `Default`)
> - 담당자 (선택)

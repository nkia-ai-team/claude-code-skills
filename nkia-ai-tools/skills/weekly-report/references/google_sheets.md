# Google Sheets Integration

`gws` (Google Workspace CLI)를 사용한 구글 시트 연동 로직을 정의합니다.

---

## 1. 시트 구조

### 1.1 스프레드시트 구조

주간업무보고 시트는 **주차별 탭(시트)** 구조입니다:

| 탭 이름 | 용도 |
|--------|------|
| `템플릿` | 빈 서식 템플릿 (숨김) |
| `20260327` | 2026년 3월 4주차 |
| `20260212` | 2026년 2월 2주차 |
| ... | 과거 주차들 |

**탭 이름 규칙:** `YYYYMMDD` — 해당 주의 **목요일 날짜** (weekEnd)

### 1.2 탭 내 레이아웃

**템플릿에서 복제되므로 고정된 레이아웃은 없습니다.** 실행 시 A열에서 작성자 이름을 동적으로 탐색하여 행 번호를 결정합니다.

현재 템플릿 구조:

| 행 | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| 1 | 주간업무보고 | | | | | | | |
| 2 | | 금주 업무 실적 | | | | 차주 업무 계획 | | 총 업무시간 |
| 3 | 보고자 | 업무구분 | 업무 (목표일, 진행율) | 업무 내용 | 투입시간 | 업무 구분 | 업무 | |
| 4+ | 팀원명 | 백로그 | (데이터) | (데이터) | | 백로그 | (데이터) | |

### 1.3 팀원 데이터 컬럼 매핑

| 열 | 헤더 | 스킬에서 채울 내용 |
|----|------|-----------------|
| C | 업무 (목표일, 진행율) | 이번주 한 일 — 번호 리스트 (요약) |
| D | 업무 내용 | 업무 내용 — 번호 + 서브불릿 (상세) |
| G | 업무 | 다음주 할 일 — 번호 리스트 |

A(보고자), B(업무구분), F(업무구분)은 템플릿에서 이미 채워져 있으므로 **C, D, G열만 기입합니다.**

### 1.4 시트 ID

- 환경변수: `WEEKLY_REPORT_SHEET_ID`
- 기본값: `17VHfLRTWJOmh9I59XWnqw3TPa8iHh9NC4iEhoJViJxQ`

---

## 2. 탭 존재 확인 및 생성

### 2.1 탭 목록 조회

    gws sheets spreadsheets get \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\", \"fields\": \"sheets.properties\"}" \
      --format json 2>/dev/null

응답에서 `sheets[].properties.title`을 탐색하여 `YYYYMMDD` 탭이 존재하는지 확인합니다.

### 2.2 탭이 존재하는 경우

해당 탭에서 **작성자 이름으로 행 번호를 동적 탐색합니다:**

    gws sheets spreadsheets values get \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\", \"range\": \"${TAB}!A1:A20\"}" \
      --format json 2>/dev/null

응답의 `values` 배열에서 작성자 이름이 있는 인덱스 → 행 번호 = 인덱스 + 1

**작성자 행에 이미 데이터가 있는 경우:**

    이번 주({{tabName}}) 탭에 {{author}}의 데이터가 이미 있습니다.
    덮어쓰시겠습니까? (y/n)

### 2.3 탭이 존재하지 않는 경우 — 템플릿 복제

**Step 1: 템플릿 탭 복제**

`batchUpdate`의 `duplicateSheet`로 "템플릿" 탭을 복제합니다.

먼저 Section 2.1의 탭 목록 조회 응답에서 `title == "템플릿"`인 탭의 `sheetId`를 추출합니다:

    sheets[].properties에서 title == "템플릿" → sheetId 추출 → TEMPLATE_SHEET_ID

그 후 복제합니다:

    gws sheets spreadsheets batchUpdate \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\"}" \
      --json "{\"requests\": [{\"duplicateSheet\": {\"sourceSheetId\": ${TEMPLATE_SHEET_ID}, \"insertSheetIndex\": 1, \"newSheetName\": \"${TAB_NAME}\"}}]}" \
      2>/dev/null

- `insertSheetIndex: 1` — "템플릿" 탭 다음에 삽입 (최신 주가 위에 오도록)
- 복제된 탭은 서식(셀 병합, 배경색, 테두리, 글꼴) + 헤더 + 팀원명 + 백로그 구분이 **모두 포함**되어 있어 데이터만 기입하면 됨

**Step 2: 숨김 해제** (템플릿이 숨김 상태인 경우 복제본도 숨김이 됨)

    gws sheets spreadsheets batchUpdate \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\"}" \
      --json "{\"requests\": [{\"updateSheetProperties\": {\"properties\": {\"sheetId\": ${NEW_SHEET_ID}, \"hidden\": false}, \"fields\": \"hidden\"}}]}" \
      2>/dev/null

`NEW_SHEET_ID`는 Step 1 응답의 `replies[0].duplicateSheet.properties.sheetId`에서 추출합니다.

---

## 3. 데이터 기입

### 3.1 작성자 행 탐색

탭의 A열 전체를 읽어 작성자 이름의 행 번호를 찾습니다:

    gws sheets spreadsheets values get \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\", \"range\": \"${TAB}!A1:A20\"}" \
      --format json 2>/dev/null

응답의 `values` 배열에서 작성자 이름 매칭 → 행 번호 = 배열 인덱스 + 1

### 3.2 C, D열 기입 (금주 요약 + 상세)

    gws sheets spreadsheets values update \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\", \"range\": \"${TAB}!C${ROW}:D${ROW}\", \"valueInputOption\": \"USER_ENTERED\"}" \
      --json "$(cat temp/weekly-report-payload.json)" 2>/dev/null

페이로드 JSON:

    {
      "values": [
        ["금주 요약 내용", "금주 상세 내용"]
      ]
    }

### 3.3 G열 기입 (차주 계획)

    gws sheets spreadsheets values update \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\", \"range\": \"${TAB}!G${ROW}:G${ROW}\", \"valueInputOption\": \"USER_ENTERED\"}" \
      --json "$(cat temp/weekly-report-next.json)" 2>/dev/null

페이로드 JSON:

    {
      "values": [
        ["차주 계획 내용"]
      ]
    }

### 3.4 안전한 페이로드 생성

JSON 문자열을 직접 셸에서 조합하면 이스케이프 오류가 발생하기 쉽습니다. **반드시 임시 파일을 사용합니다:**

1. `Write` 도구로 `temp/weekly-report-payload.json`, `temp/weekly-report-next.json` 생성
2. `Bash`에서 `--json "$(cat temp/weekly-report-*.json)"` 으로 전달
3. 완료 후 임시 파일 삭제

### 3.5 줄바꿈 처리

셀 내 줄바꿈은 JSON 문자열의 `\n`으로 표현합니다. `valueInputOption: USER_ENTERED`이므로 시트에서 줄바꿈이 올바르게 렌더링됩니다.

    "1. 항목A\n2. 항목B\n3. 항목C"

서브불릿:

    "1. 제목\n- 서브불릿1\n- 서브불릿2\n\n2. 제목\n- 서브불릿1"

---

## 4. gws CLI 참고

### 4.1 stderr 분리

gws는 stderr에 `Using keyring backend: keyring` 등을 출력합니다. JSON 파싱 시 **반드시 `2>/dev/null`로 stderr를 분리합니다.**

### 4.2 range 파라미터

탭 이름이 영문/숫자인 경우 raw API를 사용합니다:

    gws sheets spreadsheets values get \
      --params "{\"spreadsheetId\": \"${SHEET_ID}\", \"range\": \"20260327!A1:G10\"}" 2>/dev/null

### 4.3 인증

gws는 OAuth2로 인증됩니다. 인증 상태 확인:

    gws auth status

인증 만료 시:

    gws auth login

---

## 5. Error Handling

### 5.1 인증 만료

    ERROR: gws 인증이 만료되었습니다.
    `gws auth login`으로 재인증해주세요.

### 5.2 시트 접근 권한 없음

    ERROR: 시트에 접근할 수 없습니다. 시트 ID를 확인하거나 공유 설정을 확인해주세요.
    시트 ID: {{SHEET_ID}}

### 5.3 쓰기 실패

    ERROR: 시트 쓰기에 실패했습니다.
    {{error_message}}

    렌더링된 보고서를 출력합니다. 수동으로 시트에 복사해주세요:
    [렌더링된 내용]

자동 재시도는 하지 않습니다. 렌더링된 내용을 출력하여 수동 복사를 안내합니다.

### 5.4 환경변수 미설정

    WEEKLY_REPORT_SHEET_ID가 설정되지 않았습니다.
    구글 시트 URL 또는 ID를 입력해주세요:

URL이 입력된 경우 시트 ID를 추출합니다:

    https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0
    → SHEET_ID 추출

### 5.5 템플릿 탭 없음

    ERROR: "템플릿" 탭을 찾을 수 없습니다.
    시트에 "템플릿" 이름의 숨김 탭이 있는지 확인해주세요.

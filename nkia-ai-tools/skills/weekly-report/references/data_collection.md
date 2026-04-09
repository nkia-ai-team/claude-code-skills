# Weekly Report Data Collection

주간 업무 보고서를 위한 데이터 수집 로직을 정의합니다.

---

## 1. 주간 범위 계산

주간 보고는 **금요일~목요일** 단위로 집계합니다 (가이드라인과 동일).

- **이번 주** = 지난주 금요일 ~ 이번주 목요일
- 기본값: 오늘 날짜 기준 이번 주
- `--week 2026-04-09` → 2026-04-03 (금) ~ 2026-04-09 (목)

**주간 시작/끝 계산:**

    dayOfWeek = 기준일.getDayOfWeek()  // 0=일, 1=월, ..., 5=금, 6=토
    if dayOfWeek >= 5 (금~토):
      weekStart = 기준일 - (dayOfWeek - 5)일  // 이번주 금요일
    else:
      weekStart = 기준일 - (dayOfWeek + 2)일  // 지난주 금요일
    weekEnd = weekStart + 6일 (목요일)
    thursdayDate = weekEnd  // 시트 탭 이름에 사용

---

## 2. Linear 이슈 수집

### 2.1 이번 주 이슈 조회

**아래 2개 조회를 병렬로 실행합니다:**

| # | 용도 | API 호출 |
|---|------|----------|
| 2.1a | 이번 주 활동 이슈 | `mcp__linear__list_issues(assignee: "me", updatedAt: weekStart)` |
| 2.1b | 다음 사이클/Todo 이슈 | `mcp__linear__list_issues(assignee: "me", state: "Todo")` |

### 2.2 이슈 분류

조회된 이슈를 다음과 같이 분류합니다:

| 카테고리 | 분류 기준 | 용도 |
|---------|----------|------|
| **done_issues** | state가 "Done"이고 completedAt이 이번 주 범위 내 | 금주 실적 — 완료 항목 |
| **in_progress_issues** | state가 "In Progress"이고 updatedAt이 이번 주 | 금주 실적 — 진행 중 항목 |
| **todo_issues** | state가 "Todo" (사이클 배정 여부 무관) | 차주 계획 |

**분류 우선순위** (하나의 이슈가 여러 카테고리에 해당 시):
1. done_issues (최우선)
2. in_progress_issues
3. todo_issues

### 2.3 이슈 상세 조회

분류된 이슈 중 done_issues와 in_progress_issues에 대해 `mcp__linear__get_issue`를 **병렬 호출**하여 attachments를 포함한 상세 정보를 가져옵니다.

필요 필드:
- **title**: 이슈 제목 (`[AC 요청]`, `[AC 확인]` 접미사 제거)
- **description**: AC 항목, 작업 내용 추출용
- **labels**: 라벨 (Bug, Feature, Improvement 등)
- **attachments**: MR/PR URL → 레포 식별
- **project**: 프로젝트명 (업무 그룹핑)

---

## 3. 레포 식별 — Attachment URL 파싱

이슈의 `attachments[].url`에서 MR/PR URL을 파싱하여 레포를 식별합니다.

### GitLab MR URL 패턴

    https://cims2.nkia.net:8443/gitlab/{repo-name}/-/merge_requests/{mr-number}

추출 정규식:

    /gitlab\/([^/]+)\/-\/merge_requests/

예시:
- `cims2.nkia.net:8443/gitlab/lucida-chat-ai/-/merge_requests/116` → `lucida-chat-ai`
- `cims2.nkia.net:8443/gitlab/lucida-ui/-/merge_requests/15707` → `lucida-ui`

### GitHub PR URL 패턴

    https://github.com/{owner}/{repo}/pull/{pr-number}

추출 정규식:

    /github\.com\/[^/]+\/([^/]+)\/pull/

### Attachment가 없는 이슈

attachment가 없는 이슈(예: In Progress 상태, 아직 MR 미생성)는 레포 식별을 건너뜁니다.
해당 이슈의 커밋은 수집하지 않으며, Linear 이슈 정보만으로 보고서를 작성합니다.

### 레포 중복 제거

여러 이슈에서 동일 레포가 식별되면 한 번만 커밋을 수집합니다.

---

## 4. Git 커밋 수집

식별된 레포별로 이번 주 커밋을 수집합니다.

### 4.1 레포 경로 탐색

식별된 레포 이름으로 로컬 디렉토리를 탐색합니다:

    # 현재 워킹 디렉토리의 부모/형제 디렉토리에서 탐색
    find ~/Desktop/DEV -maxdepth 1 -name "{repo-name}" -type d

로컬에서 찾을 수 없는 레포는 건너뜁니다 (경고 메시지 출력).

### 4.2 커밋 로그 조회

해당 레포 디렉토리에서 이번 주 범위의 본인 커밋을 조회합니다:

    git -C {repo-path} log \
      --author="{reporterName}" \
      --after="{weekStart}" \
      --before="{weekEnd + 1일}" \
      --pretty=format:"%h %s" \
      --all

### 4.3 커밋-이슈 매핑

커밋 메시지에서 이슈 번호를 추출하여 해당 이슈에 매핑합니다:

    # 커밋 메시지 패턴
    nkiaai-{number} {Type} : {description}
    #{pims} {Type} : {description} nkiaai-{number}

추출 정규식:

    /nkiaai-(\d+)/i

매핑된 커밋은 해당 이슈의 상세 업무 내용(D열)을 보강하는 데 사용됩니다.
이슈에 매핑되지 않는 커밋은 "기타" 항목으로 별도 수집합니다.

---

## 5. Google Calendar 이벤트 수집

### 5.1 캘린더 이벤트 조회

`gws` CLI로 이번 주 범위의 캘린더 이벤트를 조회합니다:

    gws calendar events list \
      --params '{"calendarId": "{calendarName}", "timeMin": "{weekStart}T00:00:00+09:00", "timeMax": "{weekEnd}T23:59:59+09:00", "singleEvents": true}'

**주의:** `calendarId`에 캘린더 이름이 안 먹는 경우, 먼저 캘린더 목록을 조회하여 ID를 얻습니다:

    gws calendar calendarList list

캘린더 목록에서 `summary`가 config의 `calendarName`과 일치하는 항목의 `id`를 사용합니다.

### 5.2 본인 이벤트 필터링

조회된 이벤트 중 **creator.email이 config의 googleEmail과 일치**하는 이벤트만 필터링합니다.

### 5.3 휴가/반차 판별

필터링된 이벤트에서 휴가/반차 키워드를 포함하는 이벤트를 식별합니다:

**키워드 목록:**

| 키워드 | 분류 |
|--------|------|
| `연차`, `휴가`, `vacation`, `day off` | 연차 |
| `반차`, `오전반차`, `오후반차`, `half day` | 반차 |
| `병가`, `sick leave` | 병가 |

**판별 로직:**
1. 이벤트 제목(summary)에 키워드 포함 여부 확인
2. 종일 이벤트(allDay) 여부로 연차/반차 추가 판별
3. 키워드 매칭이 안 되면 스킵 (일반 회의 등은 제외)

### 5.4 수집 결과 형식

    [
      { "date": "2026-04-07", "type": "오전반차", "summary": "오전반차 방성준" },
      { "date": "2026-04-08", "type": "연차", "summary": "연차 방성준" }
    ]

---

## 6. Error Handling

### Linear API 실패

    WARN: Linear 이슈 조회에 실패했습니다. Git 커밋과 Calendar 데이터만으로 보고서를 구성합니다.

### Git 레포 미발견

    WARN: 레포 "lucida-chat-ai"의 로컬 경로를 찾을 수 없습니다. 해당 레포 커밋은 건너뜁니다.

### gws Calendar 조회 실패

    WARN: Google Calendar 조회에 실패했습니다. 휴가/반차 정보 없이 보고서를 구성합니다.
    인증 확인: gws auth login

### 모든 소스 실패

    ERROR: 모든 데이터 소스(Linear, Git, Calendar)에서 데이터를 가져올 수 없습니다.
    네트워크 연결 및 인증 상태를 확인해주세요.

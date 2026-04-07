# Weekly Report Data Collection

주간업무일지를 위한 데이터 수집 로직을 정의합니다.

---

## 1. 주간 범위 계산

주간업무일지는 **금요일~목요일** 단위로 집계합니다.

- **이번 주** = 지난주 금요일 ~ 이번주 목요일
- **다음 주** = 이번주 금요일 ~ 다음주 목요일
- 기본값: 오늘 날짜 기준 이번 주
- `--week 2026-03-20` → 2026-03-20이 속한 금~목 주간

**주간 시작/끝 계산:**

    dayOfWeek = 기준일.getDayOfWeek()  // 0=일, 1=월, ..., 5=금, 6=토
    if dayOfWeek >= 5 (금~토):
      weekStart = 기준일 - (dayOfWeek - 5)일  // 이번주 금요일
    else:
      weekStart = 기준일 - (dayOfWeek + 2)일  // 지난주 금요일
    weekEnd = weekStart + 6일 (목요일)

**날짜 라벨 계산:**

| 항목 | 계산 | 예시 |
|------|------|------|
| 주차 구분 | `weekEnd`의 월 + 주차 | 3월 4주차 |
| 이번 주(목) | `weekEnd` | 2026/03/26 |
| 다음 주(목) | `weekEnd + 7일` | 2026/04/02 |

**주차 번호 계산:**
해당 월의 첫 번째 목요일이 속한 주를 1주차로 하고, `weekEnd`(목요일)가 몇 번째 주에 속하는지 계산합니다.

---

## 2. Linear 이슈 수집

### 2.1 이슈 목록 조회

**아래 조회를 병렬로 실행합니다:**

| # | 용도 | API 호출 |
|---|------|----------|
| A | 이번 주 활동 이슈 | `list_issues(assignee: "me", updatedAt: weekStart)` |
| B | In Progress 이슈 | `list_issues(assignee: "me", state: "In Progress")` |
| C | Todo 이슈 | `list_issues(assignee: "me", state: "Todo")` |

- 조회 A: "이번주 한 일" + "업무 내용" 생성용
- 조회 B, C: "다음주 할 일" 생성용

### 2.2 이슈 상세 조회 (MR 역추적)

조회 A에서 나온 이슈를 `get_issue`로 상세 조회합니다. **병렬로 실행합니다.**

`get_issue` 응답에서 추출할 데이터:

| 필드 | 용도 |
|------|------|
| `title` | 이슈 제목 (요약 리스트) |
| `description` | AC/목표에서 성과 내용 추출 |
| `status` | 분류 기준 (Done, In Progress, In Review 등) |
| `labels` | 분류 보조 (Feature, Improvement, Bug 등) |
| `attachments[].url` | GitLab MR URL 역추적 |
| `gitBranchName` | MR이 없는 경우 브랜치명으로 보조 |
| `project.name` | 프로젝트 그룹화 (선택) |

### 2.3 이슈 분류

수집된 이슈를 상태 기반으로 분류합니다:

| 카테고리 | 분류 기준 | 보고서 반영 위치 |
|---------|----------|---------------|
| **done** | status == "Done" 이고 updatedAt이 이번 주 | 이번주 한 일 + 업무 내용 |
| **in_review** | status == "In Review" 이고 updatedAt이 이번 주 | 이번주 한 일 + 업무 내용 |
| **in_progress** | status == "In Progress" 이고 updatedAt이 이번 주 | 이번주 한 일 + 업무 내용 + 다음주 할 일 |
| **new** | createdAt이 이번 주 범위 내 | 업무 내용 (신규 등록) |

**분류 우선순위** (한 이슈가 여러 카테고리에 해당할 때):
1. done
2. in_review
3. in_progress
4. new

---

## 3. GitLab MR/커밋 역추적

### 3.1 MR URL 파싱

`get_issue`의 `attachments[].url`에서 GitLab MR URL을 추출합니다.

**URL 패턴:**

    https://{host}/gitlab/{repo}/-/merge_requests/{mr_id}

**파싱:**

    url = "https://cims2.nkia.net:8443/gitlab/lucida-ui/-/merge_requests/15702"
    → host = "cims2.nkia.net:8443"
    → repo = "lucida-ui"
    → mr_id = 15702

### 3.2 MR 상세 조회

GitLab API로 MR 상세 정보를 조회합니다.

    GITLAB_HOST={host} glab api "projects/{repo}/merge_requests/{mr_id}" \
      --hostname {host}

**응답에서 추출할 데이터:**

| 필드 | 용도 |
|------|------|
| `title` | MR 제목 (업무 내용 보조) |
| `description` | MR 설명 (변경 사항 요약) |
| `merged_at` | 머지 여부/시점 확인 |
| `changes_count` | 변경 파일 수 |
| `source_branch` | 브랜치명 |

### 3.3 MR 커밋 조회

MR에 포함된 커밋 목록을 조회합니다.

    GITLAB_HOST={host} glab api "projects/{repo}/merge_requests/{mr_id}/commits" \
      --hostname {host}

**응답에서 추출할 데이터:**

| 필드 | 용도 |
|------|------|
| `title` (각 커밋) | 업무 내용의 서브불릿 생성 |
| 커밋 수 | 작업량 지표 |

### 3.4 MR이 없는 이슈

attachments가 비어있는 이슈는 MR 역추적을 건너뜁니다.

- `gitBranchName`이 있으면: 브랜치가 존재하지만 아직 MR 미생성 (진행 중)
- description의 AC 항목과 이슈 제목으로만 요약 생성

### 3.5 GitLab 프로젝트 ID 해석

`glab api`는 URL-encoded 프로젝트 경로를 사용합니다. 단순 레포명의 경우:

    projects/lucida-ui → URL-encoded: projects/lucida-ui

네임스페이스가 있는 경우:

    projects/group%2Flucida-ui

**현재 환경의 GitLab 레포는 루트 경로에 있으므로** 레포명만으로 접근 가능합니다.

---

## 4. 데이터 수집 전체 흐름

```
Step 1: 주간 범위 계산
  → weekStart, weekEnd, weekLabel

Step 2: Linear 이슈 수집 (병렬)
  ├─ list_issues(assignee=me, updatedAt=weekStart)  → 이번 주 이슈
  ├─ list_issues(assignee=me, state="In Progress")   → 진행 중 이슈
  └─ list_issues(assignee=me, state="Todo")          → 할 일 이슈

Step 3: 이슈 상세 + MR URL 추출 (병렬)
  └─ 각 이슈에 대해 get_issue → attachments[].url

Step 4: GitLab MR/커밋 조회 (병렬)
  └─ 각 MR URL에 대해 glab api → MR 상세 + 커밋 목록

Step 5: 이슈 분류
  → done, in_review, in_progress, new

Step 6: 데이터 병합
  → 이슈 + MR + 커밋 데이터를 이슈 단위로 병합
```

---

## 5. Error Handling

### Linear API 실패

    ERROR: Linear 이슈 조회에 실패했습니다.
    {{error_message}}

재시도 없이 사용자에게 알리고 중단합니다.

### GitLab API 실패

개별 MR 조회 실패는 해당 MR만 스킵하고 나머지를 계속 수집합니다.

    WARNING: MR 조회 실패 ({{repo}} !{{mr_id}}): {{error_message}}
    해당 MR 없이 보고서를 생성합니다.

### 이슈 0건

    INFO: 이번 주({{weekStart}} ~ {{weekEnd}}) 활동 이슈가 없습니다.
    보고서를 생성할 데이터가 없어 종료합니다.

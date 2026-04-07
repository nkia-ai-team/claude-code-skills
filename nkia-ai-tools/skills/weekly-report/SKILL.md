---
name: weekly-report
description: Generate weekly work reports by collecting Linear issues and GitLab MR/commit data, then writing the result to a Google Sheet tab. Use this skill when creating weekly work reports.
---

# Weekly Report — 주간업무보고 자동화

## CRITICAL: First Step — Read the References

**BEFORE generating any report, you MUST read:**
- [data_collection.md](references/data_collection.md) — 주간 범위 계산, Linear 이슈 수집, GitLab MR/커밋 역추적
- [report_rendering.md](references/report_rendering.md) — 보고서 렌더링 규칙, 시트 컬럼 매핑, 미리보기 형식
- [google_sheets.md](references/google_sheets.md) — gws CLI 사용법, 탭 구조, 탭 생성/기입 방법

---

## Overview

Linear 이슈 활동과 GitLab MR/커밋 데이터를 자동 수집하여 주간업무보고를 생성하고, 구글 시트의 **주차별 탭**에 작성자 행을 기입합니다.

**하는 일:**
- 이번 주 Linear 이슈 활동 수집 (assignee=me, updatedAt 기준)
- 각 이슈의 attachments에서 GitLab MR URL 역추적 → MR 커밋 내역 조회
- 이슈별 분류 및 요약 생성 (C열: 금주 요약, D열: 금주 상세, G열: 차주 계획)
- 구글 시트의 해당 주차 탭에 작성자 행 기입 (탭이 없으면 생성)

**하지 않는 일:**
- 레포 경로를 직접 설정/관리 (Linear → MR 역추적으로 레포를 자동 파악)
- 프로젝트별 업데이트 (→ `/linear-project-updater` 사용)
- 다른 팀원의 보고서 작성 (본인 행만 기입)

---

## Usage

    /weekly-report                                        # 이번 주, 기본값
    /weekly-report --week 2026-03-20                      # 특정 주 (해당 날짜가 속한 금~목)
    /weekly-report --next "데모 피드백 수정, 완료 리뷰 시연"   # 차주 할 일 직접 추가

**Options:**

| 옵션 | 설명 |
|-----|------|
| `--week <YYYY-MM-DD>` | 기준 주 지정 (해당 날짜가 속한 금~목). 미지정 시 이번 주 |
| `--next "<텍스트>"` | 차주 할 일에 자유 텍스트 항목 추가 (자동 생성 항목과 병합) |

---

## Workflow

### Step 1: Calculate Week Range

**금요일~목요일** 단위로 주간 범위를 계산합니다.
탭 이름은 weekEnd(목요일)를 `YYYYMMDD` 형식으로 변환합니다.

계산 로직은 [data_collection.md Section 1](references/data_collection.md) 참조

### Step 2: Check Tab & Row

구글 시트에서 해당 주차 탭이 존재하는지, 작성자 행이 있는지 확인합니다.

- **탭 존재** → A열에서 작성자 이름 동적 탐색 → 해당 행에 C/D/G열 기입
- **탭 없음** → "템플릿" 탭 복제 (서식+팀원명 완전 보존) → 숨김 해제 → C/D/G열 기입

탭 확인/생성 로직은 [google_sheets.md Section 2](references/google_sheets.md) 참조

### Step 3: Collect Data (병렬)

**아래 작업을 병렬로 실행합니다:**

1. **Linear 이슈 수집** — `list_issues(assignee=me, updatedAt=weekStart)` + 상태별 조회
2. **이슈별 상세 + MR 역추적** — `get_issue`로 attachments에서 GitLab MR URL 추출
3. **GitLab MR/커밋 조회** — `glab api`로 MR 상세 및 커밋 내역 조회

데이터 수집 로직은 [data_collection.md Section 2~4](references/data_collection.md) 참조

### Step 4: Read Existing Tab Style

이번 주 탭에 이미 다른 팀원이 작성한 데이터가 있으면 읽어서 **문체, 상세도, 형식**을 참고합니다. 같은 탭 안에서 일관된 수준의 보고서를 생성해야 합니다.

### Step 5: Classify & Render

수집된 데이터를 분류하고 시트 컬럼별 텍스트를 생성합니다.

| 컬럼 | 내용 |
|------|------|
| C (금주 요약) | 이슈 제목 기반 번호 리스트 |
| D (금주 상세) | 이슈 + MR 커밋 기반 번호 + 서브불릿 |
| G (차주 계획) | In Progress/Todo 기반 번호 리스트 + 사용자 입력 |

분류 및 렌더링 로직은 [report_rendering.md](references/report_rendering.md) 참조

### Step 6: Preview & Confirm

생성된 보고서를 미리보기로 출력한 뒤, `AskUserQuestion`으로 저장 여부를 확인합니다.

- "저장" → Step 7로 진행
- "취소" → 종료
- 자유 텍스트 → 수정 후 다시 미리보기

미리보기 형식 및 AskUserQuestion 사용법은 [report_rendering.md Section 6](references/report_rendering.md) 참조

### Step 7: Write to Sheet

확인 후 `gws sheets spreadsheets values update`로 해당 탭의 작성자 행에 데이터를 기입합니다.

시트 기입 로직은 [google_sheets.md Section 3](references/google_sheets.md) 참조

### Step 8: Show Result

    === 주간업무보고 저장 완료 ===

    탭: {{tabName}}
    행: {{rowNumber}} ({{author}})
    시트: https://docs.google.com/spreadsheets/d/{{SHEET_ID}}/edit#gid={{sheetId}}

    ==============================

---

## Prerequisites

### gws (Google Workspace CLI)

이 스킬은 구글 시트 연동에 `gws`를 사용합니다. 실행 전 설치 여부를 확인하고, 미설치 시 안내합니다:

    which gws

**미설치 시 안내 메시지:**

    gws(Google Workspace CLI)가 설치되어 있지 않습니다.
    아래 명령어로 설치 후 다시 실행해주세요:

    1. 설치: npm install -g @googleworkspace/cli
    2. 인증 설정: gws auth setup
    3. 로그인: gws auth login

    참고: https://github.com/googleworkspace/cli

설치/인증이 완료되면 스킬을 다시 실행합니다. gws 없이는 스킬이 동작하지 않습니다.

---

## Configuration

| 항목 | 환경변수 | 설명 |
|------|---------|------|
| 구글 시트 ID | `WEEKLY_REPORT_SHEET_ID` | 주간업무보고 구글 시트의 ID (기본값: `17VHfLRTWJOmh9I59XWnqw3TPa8iHh9NC4iEhoJViJxQ`) |
| 작성자 이름 | `WEEKLY_REPORT_AUTHOR` | 보고서 작성자 이름 (기본: Linear 프로필에서 추출) |

---

## Integration with Other Skills

| 스킬 | 연동 |
|-----|------|
| `/linear-project-updater` | 프로젝트별 상세 업데이트 (이 스킬은 개인 주간보고) |
| `/submit` | MR 생성 시 Linear attachments에 MR URL 자동 연결 → 이 스킬이 역추적 |
| `/wrap-up` | 이슈 완료 후 증빙 첨부 → 이 스킬이 완료 이슈 데이터 활용 |

---

## Resources

- [data_collection.md](references/data_collection.md) — 주간 범위 계산, Linear 이슈 조회, GitLab MR/커밋 역추적, 이슈 분류
- [report_rendering.md](references/report_rendering.md) — 보고서 렌더링 규칙, 컬럼별 생성 로직, 미리보기 형식
- [google_sheets.md](references/google_sheets.md) — gws CLI 사용법, 탭 구조, 탭 생성/기입 방법, 에러 처리

---
name: weekly-report
description: Generate weekly work reports by collecting Linear issues, Git commits, and Google Calendar events, then write them to the team's Google Sheets. Use this skill when writing the weekly status report on Thursdays.
---

# Weekly Report — 주간 업무 보고서 자동화

## CRITICAL: First Step — Read the References

**BEFORE generating any report, you MUST read:**
- [data_collection.md](references/data_collection.md) — Linear 이슈, Git 커밋, Google Calendar 수집 로직
- [sheet_operations.md](references/sheet_operations.md) — 구글 시트 탭/행 탐색 및 셀 기록
- [report_rendering.md](references/report_rendering.md) — 컬럼별 렌더링 규칙

---

## Overview

이번 주 Linear 이슈, Git 커밋, Google Calendar 이벤트를 자동 수집하여 팀 주간 업무 보고 구글 시트에 기록하는 스킬입니다.

**하는 일:**
- Linear 이슈 수집 (Done → 금주 실적, In Progress/Todo → 차주 계획)
- 이슈 attachments에서 레포 식별 → 해당 레포 Git 커밋 수집
- Google Calendar에서 본인 등록 휴가/반차 이벤트 조회
- 수집 데이터를 시트 컬럼 형식에 맞게 구조화
- 이번 주 목요일 날짜 탭 찾기 → 본인 행에 기록

**하지 않는 일:**
- 투입시간(E열) 계산 — 생략
- 다른 팀원의 보고서 작성
- 시트 구조/형식 변경

---

## Usage

    /weekly-report

**Options:**

| 옵션 | 설명 |
|-----|------|
| `--week <YYYY-MM-DD>` | 기준 주 지정 (해당 날짜가 속한 주의 목요일). 미지정 시 이번 주 |
| `--dry-run` | 미리보기만 (시트 기록 안 함) |
| `--reconfigure` | 저장된 설정 초기화 후 재설정 |

---

## Configuration

최초 실행 시 사용자에게 아래 정보를 입력받아 config 파일에 저장합니다.

**저장 위치:** `~/.config/nkia-ai-tools/weekly-report.json`

```json
{
  "reporterName": "방성준",
  "googleEmail": "happypigs7@gmail.com",
  "calendarName": "AI연구소",
  "spreadsheetId": "17VHfLRTWJOmh9I59XWnqw3TPa8iHh9NC4iEhoJViJxQ"
}
```

| 필드 | 설명 | 용도 |
|------|------|------|
| `reporterName` | 보고자 이름 | 시트 A열에서 본인 행 매칭 |
| `googleEmail` | 구글 이메일 | Calendar 이벤트 creator 필터링 |
| `calendarName` | 팀 캘린더 이름 | 휴가/반차 이벤트 조회 대상 |
| `spreadsheetId` | 스프레드시트 ID | 대상 시트 |

설정이 이미 존재하면 입력 없이 바로 진행합니다. `--reconfigure`로 재설정 가능합니다.

---

## Workflow

### Step 1: Check & Install gws CLI

`gws` CLI 설치 여부를 확인하고, 없으면 자동 설치합니다.

    which gws

**미설치 시 자동 설치:**

1. `npm`이 있는지 확인 → 있으면 npm으로 설치:

       npm install -g @googleworkspace/cli

2. `npm`이 없고 `brew`가 있으면 brew로 설치:

       brew install googleworkspace-cli

3. 둘 다 없으면 에러:

       ERROR: gws CLI를 설치할 수 없습니다.
       npm 또는 brew를 먼저 설치해주세요.

**설치 후 인증 확인:**

    gws auth status

인증이 안 되어 있으면 스킬에 포함된 OAuth 클라이언트 JSON을 사용하여 로그인을 안내합니다.

**OAuth 클라이언트 JSON 위치:** `references/client_secret.json` (팀 공용, 스킬에 포함)

사용자에게 아래 안내를 표시합니다:

    ---
    gws 인증 설정 필요

    Google Sheets와 Calendar API를 사용하려면 gws 로그인이 필요합니다.
    브라우저가 열리는 터미널(VS Code 터미널, 일반 터미널)에서 아래 명령어를 실행하세요:

    cp {이 스킬의 references/client_secret.json 절대경로} ~/.config/gws/client_secret.json
    gws auth login

    로그인 시 Sheets와 Calendar 스코프를 모두 선택하세요.
    완료되면 말씀해주시면 이어서 진행하겠습니다.
    ---

`{절대경로}`는 스킬 실행 시 자동으로 계산하여 표시합니다.
`~/.config/gws/` 디렉토리가 없으면 `mkdir -p ~/.config/gws`를 먼저 실행합니다.

**필요한 API 스코프:**
- `https://www.googleapis.com/auth/spreadsheets` (Sheets 읽기/쓰기)
- `https://www.googleapis.com/auth/calendar.readonly` (Calendar 읽기)

### Step 2: Load or Create Config

config 파일 존재 여부를 확인합니다.

- **존재**: 설정 로드 후 Step 3으로
- **미존재**: 사용자에게 4개 필드 순서대로 질문 → 저장 → Step 3으로

### Step 3: Determine Target Week

이번 주 목요일 날짜를 계산합니다.

- 기본값: 오늘 기준 이번 주 목요일
- `--week` 옵션: 지정된 날짜가 속한 주의 목요일
- 주간 범위: **금요일~목요일** (가이드라인과 동일)

### Step 4: Collect Data (병렬)

**아래 3개 데이터 소스를 병렬로 수집합니다:**

1. **Linear 이슈** — 내 이슈 중 이번 주 활동분
2. **Google Calendar** — 이번 주 휴가/반차 이벤트
3. **Git 커밋** — Linear 이슈 attachments에서 식별된 레포별 커밋

데이터 수집 상세 로직은 [data_collection.md](references/data_collection.md) 참조

### Step 5: Render Report

수집된 데이터를 시트 컬럼 형식에 맞게 구조화합니다.

| 컬럼 | 내용 | 소스 |
|------|------|------|
| B | 업무구분 | 기본 "백로그" |
| C | 업무 (목표일, 진행율) | Linear 이슈 제목 기반 번호 리스트 |
| D | 업무 내용 | 이슈별 상세 (커밋 기반 보강) |
| F | 차주 업무 구분 | 기본 "백로그" |
| G | 차주 업무 | 다음 사이클/Todo 이슈 기반 |

렌더링 규칙은 [report_rendering.md](references/report_rendering.md) 참조

### Step 6: Preview & Confirm

생성된 보고서를 사용자에게 미리보기로 표시합니다.

    === 주간 업무 보고서 미리보기 ===

    대상: 방성준 | 탭: 20260409 | 행: 9

    [B] 업무구분: 백로그
    [C] 업무 (목표일, 진행율):
        1. RCA 멀티턴 후속 질문 LLM 기반 답변 생성
        2. alarm_select_popup 채팅 인라인 렌더링
        3. ...

    [D] 업무 내용:
        1. RCA 멀티턴 후속 질문 LLM 기반 답변 생성
        - alarm_analysis 플러그인에 RCA 후속 질문 intent 분류 추가
        - followup intent 시 alarm_select_popup 대신 텍스트 스트리밍
        2. ...

    [F] 차주 업무 구분: 백로그
    [G] 차주 업무:
        1. RCA Agent 서비스 통합 테스트 구축
        - Tier 1 smoke test + Tier 2 E2E 테스트 완성
        ...

    📅 휴가/반차: 없음

    ================================

    이대로 시트에 기록할까요? (수정이 필요하면 말씀해주세요)

`--dry-run` 옵션이면 여기서 종료합니다.

사용자가 수정을 요청하면 해당 부분만 수정 후 다시 미리보기를 보여줍니다.

### Step 7: Write to Google Sheets

시트 탐색 및 기록 로직은 [sheet_operations.md](references/sheet_operations.md) 참조

1. 시트에서 이번 주 목요일 탭(`YYYYMMDD` 형식) 찾기
2. 해당 탭에서 A열 보고자 이름으로 행 번호 찾기
3. B~D, F~G 셀에 값 기록

### Step 8: Show Results

    === 주간 업무 보고서 작성 완료 ===

    시트: 주간 업무 보고
    탭: 20260409
    보고자: 방성준 (행 9)
    기록 항목: B, C, D, F, G

    금주 실적: 5건 (Done 4건 + 기타 1건)
    차주 계획: 2건
    휴가/반차: 없음

    ===================================

---

## Integration with Other Skills

| 스킬 | 연동 |
|-----|------|
| `/linear-project-updater` | 프로젝트 업데이트와 주간 보고는 데이터 소스가 유사하나 출력 대상이 다름 (Linear vs Google Sheets) |
| `/kickoff` | kickoff로 시작한 이슈가 이번 주 보고에 자동 반영 |
| `/wrap-up` | wrap-up으로 완료된 이슈의 MR 링크가 레포 식별에 활용 |

---

## Error Handling

### gws CLI 미설치

    ERROR: gws CLI가 설치되지 않았습니다.
    설치: npm install -g @googleworkspace/cli
    인증: gws auth setup && gws auth login

### gws 인증 만료

    ERROR: Google 인증이 만료되었습니다.
    재인증: gws auth login

### 탭을 찾을 수 없음

    ERROR: 탭 "20260409"을(를) 찾을 수 없습니다.
    시트에 해당 날짜 탭이 존재하는지 확인해주세요.

### 보고자 이름 미매칭

    ERROR: A열에서 "방성준"을(를) 찾을 수 없습니다.
    config의 reporterName이 시트에 기재된 이름과 일치하는지 확인해주세요.
    재설정: /weekly-report --reconfigure

### Linear 이슈 0건

정상 진행합니다. 커밋과 캘린더 데이터만으로 보고서를 구성하며, 데이터가 전혀 없으면 안내 메시지를 출력합니다:

    INFO: 이번 주 활동 데이터가 없습니다. 빈 보고서를 생성합니다.

---

## Resources

- [data_collection.md](references/data_collection.md) — Linear 이슈 수집, Git 커밋 수집, Google Calendar 이벤트 수집, 레포 식별 로직
- [sheet_operations.md](references/sheet_operations.md) — 구글 시트 탭 탐색, 행 탐색, 셀 기록, gws CLI 명령어
- [report_rendering.md](references/report_rendering.md) — 컬럼별 렌더링 규칙, 휴가/반차 반영, 업무 내용 구조화

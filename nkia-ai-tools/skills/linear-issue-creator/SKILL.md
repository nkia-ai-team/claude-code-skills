---
name: linear-issue-creator
description: Create well-structured Linear issues with work-specific templates (Build/Deploy, Data, Evaluation, Feature Development, Feature Improvement, Refactoring, Research, Bug Fix). Supports both manual step-by-step input and automatic generation from meeting notes or natural language text with concrete DoD (Definition of Done) and AC (Acceptance Criteria). This skill should be used when users want to create a Linear issue for any type of work task.
---

# Linear Issue Creator

## Overview

Create well-structured Linear issues with appropriate work-specific templates, improved titles, automatic label application, and **concrete, measurable DoD/AC**.

**Two creation modes:**
1. **Manual Mode** - Step-by-step template-based input
2. **Auto Mode** - Automatic extraction from meeting notes or natural language text using LLM

The goal is to:
1. Select the right work template based on task type (or auto-detect)
2. Improve issue titles to be clear and concise
3. **Generate concrete and measurable DoD (Definition of Done) items**
4. **Generate concrete and measurable AC (Acceptance Criteria) items**
5. Automatically map work templates to Linear issue types
6. Automatically apply appropriate labels
7. Auto-assign cycle based on due date
8. Generate structured descriptions with DoD/AC
9. Allow users to review and edit before creating

## DoD vs AC

**Definition of Done (DoD):**
- Process completion evidence (프로세스 완료 증빙)
- Examples: 코드 리뷰 완료, CI 빌드 성공, 리포트 첨부, 문서 작성
- Focus on "what was done"
- **Format**: `- [ ] **[필수/공통/옵셔널]** [작업 내용] → 결과물: [구체적 결과물]`

**Acceptance Criteria (AC):**
- Quality standards for deliverables (결과물 품질 기준)
- Examples: 메트릭 달성, 테스트 통과, 성능 기준 충족
- Focus on "how good it is"
- **Format**: `- [ ] **[필수/공통/옵셔널]** [품질 기준] → 결과물: [검증 가능한 결과물]`

**Make items concrete and measurable** with:
1. Checkbox format (`- [ ]`) for progress tracking
2. Priority tags (**[필수]**, **[공통]**, **[옵셔널]**)
3. Explicit deliverables (`→ 결과물: ...`)
4. Template variables for context-specific values (`{{variable_name}}`)

## Work Templates and Issue Type Mapping

8 work templates are available, each automatically mapped to a Linear issue type:

| Work Template | Issue Type | Auto Labels |
|--------------|-----------|-------------|
| 1. 빌드/배포 | Task | "build" |
| 2. 데이터 작업 | Task | "task" |
| 3. 평가 | Task | "task" |
| 4. 새로운 기능 개발 | Feature | "feature" |
| 5. 기능 개선 | Feature | "improvement" |
| 6. 리팩토링 | Feature | "improvement" |
| 7. 리서치 | Research | "research" |
| 8. 버그 수정 | Bug | "bug" |

**Available Linear labels:** bug, build, feature, improvement, research, task

---

## Auto Mode Workflow

**Use this mode when user provides meeting notes, natural language descriptions, or conversation transcripts.**

### Step 1 (Auto): Collect Natural Language Input

If not already provided, request the text:

```
회의록, 메모, 또는 자연어로 작업 내용을 입력해주세요:

예시:
"오늘 회의에서 WSS 데이터셋이 부족하다는 얘기가 나왔어.
로프 난권 데이터를 11월 25일까지 수집하고 전처리, 라벨링까지 완료해야 해.
이성원님이 담당하기로 했고, Nkia-AI 팀에서 진행."

입력:
```

### Step 2 (Auto): Extract Structured Data with LLM

**IMPORTANT: Use the Pydantic schema from `scripts/parse_natural_language.py` to extract structured JSON.**

1. Load the Pydantic schema (ParsedIssue model)
2. Analyze the natural language text
3. Extract information into structured JSON matching the schema:
   - Determine `template_type` (빌드/배포, 데이터 작업, 평가, etc.)
   - **Generate improved English `title` following the template patterns below**
   - Extract `team`, `project`, `assignee`, `priority`, `due_date` if mentioned
   - **Automatically populate `labels` based on template type**
   - Fill in template-specific fields (background, description, requirements, etc.)
   - **Generate concrete and measurable `dod_items` (Definition of Done)**
   - **Generate concrete and measurable `ac_items` (Acceptance Criteria)**

**English Title Patterns by Template Type:**
- **빌드/배포** → `Deploy [target] to [environment]`
  - Example: "Deploy Auth API to Production"
- **데이터 작업** → `Process [data] for [purpose]`
  - Example: "Process Bank dataset for training"
- **평가** → `Evaluate [target] for [metric]`
  - Example: "Evaluate Fraud Detection Model for F1-score"
- **새로운 기능 개발** → `Add [feature] to [purpose]`
  - Example: "Add trace analysis to track service calls"
- **기능 개선** → `Improve [target] to [purpose]`
  - Example: "Improve query performance to reduce latency"
- **리팩토링** → `Refactor [target] to [purpose]`
  - Example: "Refactor parser module for maintainability"
- **리서치** → `Research [topic] for [purpose]`
  - Example: "Research graph algorithms for trace analysis"
- **버그 수정** → `Fix [issue] in [target]`
  - Example: "Fix OAuth login failure for SSO users"

**Title Guidelines:**
- Use action verbs: Add, Fix, Improve, Optimize, Refactor, Deploy, Evaluate, Process, Research
- Length: 5-8 words (30-50 characters recommended)
- Be specific and concise
- Consider Linear's auto-generated branch names

**Label Selection by Template Type:**
- **빌드/배포** → ["build"]
- **데이터 작업** → ["task"]
- **평가** → ["task"]
- **새로운 기능 개발** → ["feature"]
- **기능 개선** → ["improvement"]
- **리팩토링** → ["improvement"]
- **리서치** → ["research"]
- **버그 수정** → ["bug"]

**DoD/AC Generation Guidelines:**

1. **Use checkbox format** (`- [ ]`):
   - All DoD and AC items must be checkboxes for progress tracking

2. **Specify deliverables explicitly** (using `→ 결과물:`):
   - ❌ "테스트 완료"
   - ✅ "단위 테스트 커버리지 80% 이상 달성 → 결과물: 커버리지 리포트 {{coverage_report_link}}"

3. **Use template variables for context-specific values**:
   - `{{dockerfile_path}}`, `{{ci_log_link}}`, `{{metric_name}}`, `{{threshold}}`, etc.

4. **Include evidence/proof requirements**:
   - "코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}} (리뷰어 Approve)"
   - "CI 빌드 성공 → 결과물: 빌드 로그 {{ci_log_link}}"

5. **Specify quantitative criteria with deliverables**:
   - "데이터 {{record_count}}건 이상 수집 → 결과물: 수집 데이터 경로 {{data_path}}"
   - "Null 비율 < {{null_threshold}}% → 결과물: 품질 메트릭 {{quality_report}}"
   - "API 응답 시간 < {{max_response_time}}ms → 결과물: 성능 테스트 결과 {{perf_test_result}}"

**Template-Specific DoD/AC Patterns (핵심 항목만):**

> 💡 **원칙**: DoD 2개 + AC 2개 = 총 4개 이내로 유지. 가장 중요한 검증 포인트만 포함.

**빌드/배포:**
- DoD:
  - [ ] CI 빌드 성공 및 이미지 배포 완료 → 결과물: 빌드 로그 {{ci_log_link}}
  - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}
- AC:
  - [ ] {{environment}} 환경 Healthcheck 정상 (200 OK) → 결과물: 응답 로그 {{healthcheck_log}}
  - [ ] 배포 버전({{release_version}}) 정상 반영 확인 → 결과물: 버전 스크린샷 {{version_screenshot}}

**데이터 작업:**
- DoD:
  - [ ] 데이터 파이프라인 실행 완료 → 결과물: 저장 경로 {{storage_path}}
  - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}
- AC:
  - [ ] 목표 데이터 {{record_count}}건 이상 수집 → 결과물: 데이터 경로 {{data_path}}
  - [ ] 품질 기준 충족 (Null < {{null_threshold}}%) → 결과물: 품질 리포트 {{quality_report}}

**평가:**
- DoD:
  - [ ] 평가 실행 및 결과 파일 첨부 → 결과물: 결과 파일 {{eval_result_file}}
  - [ ] 결과 분석 리포트 작성 → 결과물: 리포트 {{report_link}}
- AC:
  - [ ] 목표 지표 달성 ({{metric_name}} ≥ {{threshold}}) → 결과물: 메트릭 결과 {{metric_result}}
  - [ ] 테스트셋 정보 명시 (버전: {{dataset_version}}) → 결과물: 메타데이터 {{test_metadata}}

**새로운 기능 개발:**
- DoD:
  - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}
  - [ ] 테스트 작성 및 통과 → 결과물: 테스트 결과 {{test_result}}
- AC:
  - [ ] 요구사항 기능 정상 동작 → 결과물: 테스트 증빙 {{test_evidence}}
  - [ ] API 응답 시간 {{max_response_time}}ms 이하 → 결과물: 성능 결과 {{perf_result}}

**기능 개선:**
- DoD:
  - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}
  - [ ] 개선 전/후 비교 측정 → 결과물: 비교 리포트 {{comparison_report}}
- AC:
  - [ ] 목표 지표 달성 ({{metric_name}}: {{baseline}} → {{goal}}) → 결과물: 메트릭 {{metrics}}

**리팩토링:**
- DoD:
  - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}
  - [ ] 기존 테스트 전체 통과 → 결과물: CI 로그 {{ci_log}}
- AC:
  - [ ] 기능 동작 동일 (회귀 테스트 통과) → 결과물: 테스트 결과 {{regression_result}}

**리서치:**
- DoD:
  - [ ] 조사 결과 문서 작성 → 결과물: 문서 링크 {{summary_doc_link}}
  - [ ] 팀 리뷰 완료 → 결과물: 리뷰 기록 {{review_record}}
- AC:
  - [ ] 핵심 질문에 대한 답변 제시 → 결과물: Q&A 섹션 {{qa_section}}
  - [ ] 다음 단계 Action Item 명시 → 결과물: 액션 아이템 {{action_items}}

**버그 수정:**
- DoD:
  - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}
  - [ ] 재발 방지 테스트 추가 → 결과물: 테스트 ID {{test_case_id}}
- AC:
  - [ ] 재현 시도 시 버그 미발생 → 결과물: 재현 테스트 결과 {{reproduction_test}}
  - [ ] 배포 후 관련 에러 0건 → 결과물: 모니터링 링크 {{monitoring_link}}

Example JSON output structure:
```json
{
  "metadata": {
    "template_type": "데이터 작업",
    "title": "WSS 데이터셋 수집 및 전처리",
    "team": "Nkia-AI",
    "project": null,
    "assignee": "이성원",
    "priority": "Normal",
    "due_date": "2025-11-25",
    "labels": ["task"]
  },
  "template_data": {
    "background": "WSS 모델 학습을 위한 고품질 데이터셋 구축 필요",
    "description": "WSS 학습용 데이터 수집, 정제 및 검증 작업",
    "dod_items": [
      "데이터 파이프라인 실행 완료 → 결과물: 저장 경로 {{storage_path}}",
      "코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}"
    ],
    "ac_items": [
      "목표 데이터 {{record_count}}건 이상 수집 → 결과물: 데이터 경로 {{data_path}}",
      "품질 기준 충족 (Null < {{null_threshold}}%) → 결과물: 품질 리포트 {{quality_report}}"
    ],
    "notes": "데이터 포맷: JSONL, 최소 10,000개 샘플 확보"
  }
}
```

### Step 3 (Auto): Display Extracted Information and Offer Editing

Show the extracted information in a user-friendly format:

```
=== 자동 추출된 정보 ===

**메타데이터:**
- 템플릿 타입: 데이터 작업
- 제목: WSS 데이터셋 수집 및 전처리
- 팀: Nkia-AI
- 프로젝트: (없음)
- 담당자: 이성원
- 우선순위: Normal
- 마감일: 2025-11-25
- 라벨: task

**데이터 작업 상세:**
- 배경: WSS 모델 학습을 위한 고품질 데이터셋 구축 필요
- 작업 설명: WSS 학습용 데이터 수집, 정제 및 검증 작업

**Definition of Done (DoD):**
- 데이터 파이프라인 실행 완료 → 결과물: 저장 경로 {{storage_path}}
- 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}

**Acceptance Criteria (AC):**
- 목표 데이터 {{record_count}}건 이상 수집 → 결과물: 데이터 경로 {{data_path}}
- 품질 기준 충족 (Null < {{null_threshold}}%) → 결과물: 품질 리포트 {{quality_report}}

- 참고사항: 데이터 포맷: JSONL, 최소 10,000개 샘플 확보

========================

이 정보가 맞나요?
1. 네, 이대로 진행
2. 수정하기
3. 처음부터 다시

선택:
```

### Step 4 (Auto): Edit Mode (if user selects option 2)

Provide granular editing options:

```
수정할 항목을 선택하세요:
1. 메타데이터 (제목, 팀, 담당자, 우선순위, 마감일, 라벨)
2. 템플릿 타입 변경
3. 작업 내용 (배경, 설명, DoD, AC 등)
4. 특정 필드만 수정

선택:
```

**For option 4 (specific field editing):**
```
수정할 필드명 입력 (예: title, priority, background, dod_items, ac_items):
현재 값: [현재 값 표시]
새로운 값:

계속 수정하시겠습니까? (y/n):
```

Allow multiple edits in sequence until user confirms.

### Step 5 (Auto): Auto-assign Project Based on Content

Before assigning cycle, attempt to auto-assign a relevant project:

1. Fetch all active projects for the team using `mcp__linear__list_projects` with `team` parameter
2. Analyze the issue title and description to identify key terms and topics
3. Compare issue content with project names and descriptions
4. If a relevant project is found (high confidence match), store the project ID for issue creation
5. If no clear match or low confidence, leave project as null (do not force assignment)

**Project matching criteria:**
- Match keywords from issue title/description with project name
- Consider project status (prefer active projects over completed ones)
- Use semantic similarity for better matching (e.g., "API", "endpoint", "service" might match "API Development" project)
- Only assign if confidence is high (clear keyword overlap or semantic match)
- If multiple projects match, prefer the most recently updated project

**Example matching logic:**
- Issue: "Add authentication to user API" → Project: "API Development" ✅
- Issue: "Collect WSS dataset" → Project: "WSS Model Training" ✅
- Issue: "Fix login bug" → No clear project match → Leave as null ✅

### Step 6 (Auto): Auto-assign Cycle Based on Due Date

If `due_date` is provided:
1. Fetch team cycles using `mcp__linear__list_cycles` with the team ID
2. Parse the due_date and compare with cycle date ranges (startsAt ~ endsAt)
3. Find the cycle where the due date falls within the range
4. Store the cycle ID for later use in issue creation

**Cycle matching logic:**
- Convert due_date (YYYY-MM-DD) to ISO format for comparison
- Compare with each cycle's startsAt and endsAt timestamps
- Select the cycle where: `startsAt <= due_date < endsAt`
- If no matching cycle found, skip cycle assignment (leave as null)

### Step 7 (Auto): Generate Markdown Description and Show Preview

Generate the final markdown description based on the template type and show preview:

```
=== 생성될 이슈 미리보기 ===

제목: WSS 데이터셋 수집 및 전처리
타입: Task
팀: Nkia-AI
프로젝트: WSS Model Training (자동 매칭됨) 또는 (없음)
우선순위: Normal
담당자: 이성원
마감일: 2025-11-25
사이클: Cycle 2 (2025-11-23 ~ 2025-12-07)
라벨: task

--- 설명 ---
## 배경
WSS 모델 학습을 위한 고품질 데이터셋 구축 필요

## 작업 설명
WSS 학습용 데이터 수집, 정제 및 검증 작업

## Definition of Done (DoD)
- [ ] 데이터 파이프라인 실행 완료 → 결과물: 저장 경로 {{storage_path}}
- [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}

## Acceptance Criteria (AC)
- [ ] 목표 데이터 {{record_count}}건 이상 수집 → 결과물: 데이터 경로 {{data_path}}
- [ ] 품질 기준 충족 (Null < {{null_threshold}}%) → 결과물: 품질 리포트 {{quality_report}}

## 참고사항
데이터 포맷: JSONL, 최소 10,000개 샘플 확보
--------------

이대로 생성하시겠습니까? (y/n)
```

### Step 8 (Auto): Create Issue

Use `mcp__linear__create_issue` with all collected information including:
- Auto-assigned project ID (if found)
- Auto-assigned cycle ID (if found)
- Template-based labels

Then display the result URL with project information if assigned.

---

## Manual Mode Workflow

**IMPORTANT: Quick issue creation by collecting all necessary information at once.**

### Step 1 (Manual): Collect Basic Information at Once

First, fetch available teams using `mcp__linear__list_teams`, then present ALL basic questions in a single form:

```
Linear 이슈를 생성하겠습니다. 다음 정보를 입력해주세요:

1. 작업 템플릿:
   1) 빌드/배포
   2) 데이터 작업
   3) 평가
   4) 새로운 기능 개발
   5) 기능 개선
   6) 리팩토링
   7) 리서치
   8) 버그 수정

2. 팀 이름: (사용 가능한 팀: [팀 목록])
3. 프로젝트 이름: (선택사항, 없으면 엔터)
4. 이슈 제목:
5. 우선순위: (Urgent/High/Normal/Low, 선택사항)
6. 담당자: (이름/이메일/'me', 선택사항)
7. 마감일: (YYYY-MM-DD, 선택사항)
```

**사용자가 한 번에 답변하는 예시:**
```
1. 2
2. Nkia-AI
3.
4. WSS 데이터셋 수집
5. Normal
6. me
7. 2025-11-30
```

### Step 2 (Manual): Suggest Improved Title

Analyze the provided title and suggest an improved version following these guidelines:

**Good title characteristics:**
- **Action-oriented** (uses verbs)
- **Specific and concise** (avoid vague terms)
- **Clear scope and impact**

**Examples:**
- ❌ "빌드" → ✅ "RCA 에이전트 v2.0 개발 서버 배포"
- ❌ "데이터 작업" → ✅ "WSS 데이터셋 수집 및 검증"
- ❌ "평가" → ✅ "RCA 모델 정확도 평가 (Acc@3)"
- ❌ "버그 수정" → ✅ "OAuth 로그인 실패 오류 수정"

Present the improved title:
```
제안된 제목: "WSS 데이터셋 수집 및 검증"
이 제목으로 진행하시겠습니까? (y/n, 또는 다른 제목 입력)
```

### Step 3 (Manual): Collect Template-Specific Details with DoD/AC

Based on the selected work template, request information including DoD/AC items. Use slash command examples as reference.

**For 데이터 작업:**
```
데이터 작업 상세 정보를 입력해주세요:

1. 배경 (왜 필요?):
2. 작업 설명 (어떤 데이터? 목표 품질은?):

3. Definition of Done (DoD) - 프로세스 완료 증빙 (2개 권장):
   예시:
   - [ ] 데이터 파이프라인 실행 완료 → 결과물: 저장 경로 {{storage_path}}
   - [ ] 코드 리뷰 완료 → 결과물: PR 링크 {{pr_link}}

입력:
- [ ]
- [ ]

4. Acceptance Criteria (AC) - 결과물 품질 기준 (2개 권장):
   예시:
   - [ ] 목표 데이터 {{record_count}}건 이상 수집 → 결과물: 데이터 경로 {{data_path}}
   - [ ] 품질 기준 충족 (Null < {{null_threshold}}%) → 결과물: 품질 리포트 {{quality_report}}

입력:
- [ ]
- [ ]

5. 참고사항 (선택, 데이터 소스/포맷/저장 위치):
```

### Step 4 (Manual): Apply Issue Type and Labels Automatically

Based on the selected work template, automatically:
1. Map to the appropriate Linear issue type (Task/Feature/Research/Bug)
2. Apply template-specific labels
3. Add content-based additional labels

### Step 4.5 (Manual): Auto-assign Project Based on Content

After collecting basic information and before cycle assignment, attempt to auto-assign a relevant project:

1. Fetch all active projects for the team using `mcp__linear__list_projects` with `team` parameter
2. Analyze the issue title and template details to identify key terms and topics
3. Compare issue content with project names and descriptions
4. If a relevant project is found (high confidence match), store the project ID for issue creation
5. If no clear match or low confidence, leave project as null (do not force assignment)

**Project matching criteria:**
- Match keywords from issue title/description with project name
- Consider project status (prefer active projects over completed ones)
- Use semantic similarity for better matching
- Only assign if confidence is high (clear keyword overlap or semantic match)
- If multiple projects match, prefer the most recently updated project

### Step 4.6 (Manual): Auto-assign Cycle Based on Due Date

If `due_date` is provided in Step 1:
1. Fetch team cycles using `mcp__linear__list_cycles` with the team ID
2. Parse the due_date and compare with cycle date ranges (startsAt ~ endsAt)
3. Find the cycle where the due date falls within the range
4. Store the cycle ID for later use in issue creation

**Cycle matching logic:**
- Convert due_date (YYYY-MM-DD) to ISO format for comparison
- Compare with each cycle's startsAt and endsAt timestamps
- Select the cycle where: `startsAt <= due_date < endsAt`
- If no matching cycle found, skip cycle assignment (leave as null)

### Step 5 (Manual): Show Preview and Confirm

Display the formatted issue preview with all collected information:

```
=== 생성될 이슈 미리보기 ===

제목: [개선된 제목]
타입: [자동 매핑된 이슈 타입]
팀: [팀]
프로젝트: [프로젝트명] (자동 매칭됨) 또는 (없음)
우선순위: [우선순위]
담당자: [담당자]
마감일: [마감일]
사이클: [자동 배정된 사이클] (if found)
라벨: [자동 선택된 라벨들]

--- 설명 ---
## 배경
[사용자 입력 내용]

## 작업 설명
[사용자 입력 내용]

## Definition of Done (DoD)
- [ ] [DoD 항목 1] → 결과물: [결과물]
- [ ] [DoD 항목 2] → 결과물: [결과물]

## Acceptance Criteria (AC)
- [ ] [AC 항목 1] → 결과물: [결과물]
- [ ] [AC 항목 2] → 결과물: [결과물]

## 참고사항
[사용자 입력 내용]
--------------

이대로 생성하시겠습니까? (y/n)
```

### Step 6 (Manual): Create the Issue

Use `mcp__linear__create_issue` with all collected information including:
- Auto-assigned project ID (if found)
- Auto-assigned cycle ID (if found)
- Template-based labels

Then display the result URL with project information if assigned.

---

## Important Guidelines

### 1. Title Improvement
Always suggest improved, clear titles with these characteristics:
- **Action-oriented** - Use verbs
- **Specific and concise** - Avoid vague terms
- **Clear scope and impact**

### 2. Label Selection
Automatically select labels based on work template type:
- **빌드/배포** → "build"
- **데이터 작업** → "task"
- **평가** → "task"
- **새로운 기능 개발** → "feature"
- **기능 개선** → "improvement"
- **리팩토링** → "improvement"
- **리서치** → "research"
- **버그 수정** → "bug"

**IMPORTANT:** Only use labels that exist in the Linear workspace: bug, build, feature, improvement, research, task. Do not create or suggest custom labels.

### 3. DoD/AC Management
- **Keep it minimal**: DoD 2개 + AC 2개 = 총 4개 이내 권장
- **Be concrete and measurable**: Use specific numbers, metrics, links
- **Use template variables**: `{{variable_name}}` for context-specific values
- **Include evidence**: Specify what proof is needed (links, reports, logs)

### 4. Content Focus
- Keep descriptions clear but not overly detailed
- Use DoD for process steps, AC for quality standards
- Add "참고사항" section only when there is relevant additional context

### 5. Project Auto-Assignment
- Fetch active projects for the team using `mcp__linear__list_projects`
- Analyze issue title/description for keywords and semantic matches
- Match with project names/descriptions using keyword overlap and semantic similarity
- Only assign if confidence is high (clear match)
- If no clear match, leave project as null - do not force assignment
- Prefer recently updated projects if multiple matches found

### 6. Validation
- Verify team exists using `mcp__linear__list_teams`
- Verify project exists using `mcp__linear__list_projects` (if specified by user or auto-assigned)
- Show final structure preview before creating issue

## Quick Process Principles

1. **Collect information in batches** - Present forms, not individual questions
2. **Mark optional fields clearly** - Use "(선택)" or "(선택사항)"
3. **Provide examples** - Show users how to respond with concrete DoD/AC examples
4. **Single final confirmation** - Confirm only once after collecting all information

## Pydantic Schema for Auto Mode

When using Auto Mode, the LLM should extract structured data matching the Pydantic models defined in `scripts/parse_natural_language.py`.

**Key models:**
- `ParsedIssue` - Top-level container with metadata and template_data
- `IssueMetadata` - Contains template_type, title, team, project, assignee, priority, due_date, labels
- Template-specific models with `dod_items` and `ac_items`:
  - `BuildDeployTemplate` - For 빌드/배포
  - `DataWorkTemplate` - For 데이터 작업
  - `EvaluationTemplate` - For 평가
  - `FeatureNewTemplate` - For 새로운 기능 개발
  - `FeatureImproveTemplate` - For 기능 개선
  - `RefactoringTemplate` - For 리팩토링
  - `ResearchTemplate` - For 리서치
  - `BugTemplate` - For 버그 수정

All templates now include:
- `dod_items: List[str]` - Definition of Done items
- `ac_items: List[str]` - Acceptance Criteria items

The LLM should generate concrete, measurable items with template variables when extracting from natural language.
